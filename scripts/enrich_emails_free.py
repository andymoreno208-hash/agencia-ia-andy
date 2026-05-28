#!/usr/bin/env python3
"""
Enriquecimiento GRATIS: extrae emails de la columna `website` (sin Hunter/Apollo).

Qué hace:
  - mailto:, JSON-LD, regex en HTML
  - Emails ofuscados: [at], (at), &#64;, Cloudflare data-cfemail
  - Rutas /contacto, /contact, … + enlaces internos con "contact|correo|…"
  - Sitemap/robots (si el servidor responde)
  - Log por dominio (fetch_ok / blocked / emails)

IMPORTANTE: ejecutar en TU Mac (WiFi), no desde agentes en la nube:
  muchos hosts devuelven 403 a IPs de datacenter. Instagram/Facebook no sirven.

Uso:
  python3 scripts/enrich_emails_free.py \\
    campaign_outputs/dataset_places_ec_prep.csv \\
    --sep ';' \\
    -o campaign_outputs/instantly_from_ec_prep.csv \\
    --enriched-out campaign_outputs/dataset_places_ec_enriched.csv
"""

from __future__ import annotations

import argparse
import csv
import html as html_lib
import json
import re
import ssl
import sys
import time
import multiprocessing as mp
import platform
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

try:
    import cloudscraper  # type: ignore

    HAS_CLOUDSCRAPER = True
except ImportError:
    HAS_CLOUDSCRAPER = False

CONTACT_PATHS = (
    "",
    "/contact",
    "/contacto",
    "/contacto/",
    "/contacts",
    "/es/contacto",
    "/en/contact",
    "/paginas/contactanos",
    "/contactanos",
    "/about",
    "/nosotros",
    "/equipo",
    "/team",
    "/ventas",
    "/ubicacion",
    "/ubicación",
)

URL_HINTS = (
    "contact",
    "contacto",
    "nosotros",
    "about",
    "equipo",
    "team",
    "correo",
    "escrib",
    "mail",
    "ventas",
)

SKIP_HOST = (
    "instagram.com",
    "facebook.com",
    "fb.com",
    "tiktok.com",
    "twitter.com",
    "x.com",
    "linkedin.com",
    "youtube.com",
    "youtu.be",
    "wa.me",
    "maps.google",
    "g.co",
    "bluepillow.com",
)

EMAIL_RE = re.compile(
    r"[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@"
    r"[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?"
    r"(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)+",
    re.IGNORECASE,
)
MAILTO_RE = re.compile(
    r"mailto:\s*([a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[^\"'\s>]+)",
    re.IGNORECASE,
)
CFEMAIL_RE = re.compile(
    r'data-cfemail=["\']([0-9a-fA-F]+)["\']',
    re.IGNORECASE,
)
OBFUSC_RE = re.compile(
    r"([a-zA-Z0-9._%+-]+)\s*(?:\[at\]|\(at\)|\s+at\s+|&#64;|@)\s*"
    r"([a-zA-Z0-9.-]+)\s*(?:\[dot\]|\(dot\)|\s+dot\s+|&#46;|\.)\s*([a-zA-Z]{2,10})",
    re.IGNORECASE,
)
HREF_RE = re.compile(
    r"""<a[^>]+href=["']([^"']+)["'][^>]*>""",
    re.IGNORECASE,
)
LD_JSON = re.compile(
    r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>',
    re.IGNORECASE | re.DOTALL,
)

BLOCKED_LOCAL = frozenset(
    {
        "noreply",
        "no-reply",
        "donotreply",
        "mailer-daemon",
        "postmaster",
        "webmaster",
        "abuse",
        "privacy",
        "legal",
        "newsletter",
        "bounce",
    }
)
LOW_LOCAL = frozenset(
    {"info", "contact", "contacto", "ventas", "hello", "hola", "sales", "support", "soporte", "mail"}
)
PLACEHOLDER_DOM = frozenset({"example.com", "test.com", "localhost", "sentry.io", "wixpress.com"})

# Dominios que cuelgan la red en macOS — se saltan (quedan en log como timeout)
HARD_SKIP_DOMAINS = frozenset(
    {
        "beautybyrenee.com",
    }
)

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
)


def norm_email(raw: str) -> str | None:
    e = raw.strip().strip('"').strip("'").rstrip(".,);")
    if "@" not in e:
        return None
    el = e.lower()
    if el.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg")):
        return None
    if not EMAIL_RE.fullmatch(el):
        return None
    local, _, dom = el.partition("@")
    if dom in PLACEHOLDER_DOM or local in BLOCKED_LOCAL:
        return None
    return el


def decode_cfemail(hex_str: str) -> str | None:
    try:
        key = int(hex_str[:2], 16)
        out = "".join(chr(int(hex_str[i : i + 2], 16) ^ key) for i in range(2, len(hex_str), 2))
        return norm_email(out)
    except (ValueError, IndexError):
        return None


def should_skip(url: str) -> bool:
    if not url or not url.startswith(("http://", "https://")):
        return True
    low = url.lower()
    return any(s in low for s in SKIP_HOST)


def canonicalize(raw: str) -> str | None:
    s = (raw or "").strip().strip('"')
    if not s:
        return None
    if s.startswith("//"):
        s = "https:" + s
    if not s.startswith("http"):
        s = "https://" + s
    p = urllib.parse.urlsplit(s)
    if not p.netloc:
        return None
    return urllib.parse.urlunsplit((p.scheme or "https", p.netloc, p.path or "/", p.query, ""))


def join_url(base: str, path: str) -> str:
    return urllib.parse.urljoin(base.rstrip("/") + "/", path.lstrip("/")) if path else base


def url_variants(url: str) -> list[str]:
    p = urllib.parse.urlsplit(url)
    hosts = [p.netloc]
    if p.netloc.startswith("www."):
        hosts.append(p.netloc[4:])
    else:
        hosts.append("www." + p.netloc)
    seen: set[str] = set()
    out: list[str] = []
    for h in hosts:
        for sch in ("https", "http"):
            u = urllib.parse.urlunsplit((sch, h, p.path or "/", p.query, p.fragment))
            if u not in seen:
                seen.add(u)
                out.append(u)
    return out


class Fetcher:
    def __init__(self, timeout: float, use_cloudscraper: bool) -> None:
        self.timeout = timeout
        self.ctx = ssl.create_default_context()
        self.session = None
        if use_cloudscraper and HAS_CLOUDSCRAPER:
            self.session = cloudscraper.create_scraper(
                browser={"browser": "chrome", "platform": "darwin", "desktop": True}
            )

    def get(self, url: str) -> tuple[str | None, str]:
        headers = {
            "User-Agent": UA,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "es-EC,es;q=0.9,en;q=0.8",
            "Accept-Encoding": "identity",
            "Cache-Control": "no-cache",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
        }
        last_err = ""
        for u in url_variants(url):
            try:
                if self.session:
                    r = self.session.get(u, timeout=self.timeout, headers=headers)
                    if r.status_code >= 400:
                        last_err = f"HTTP {r.status_code}"
                        continue
                    return r.text, ""
                req = urllib.request.Request(u, headers=headers, method="GET")
                with urllib.request.urlopen(req, timeout=self.timeout, context=self.ctx) as resp:
                    raw = resp.read(2_500_000)
                return raw.decode("utf-8", errors="replace"), ""
            except Exception as e:
                last_err = str(e)[:200]
        return None, last_err or "fetch_failed"


def strip_tags(html: str) -> str:
    html = re.sub(r"(?is)<script[^>]*>.*?</script>", " ", html)
    html = re.sub(r"(?is)<style[^>]*>.*?</style>", " ", html)
    html = re.sub(r"(?is)<[^>]+>", " ", html)
    return html_lib.unescape(html)


def walk_json(obj: object, found: set[str]) -> None:
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k.lower() in ("email", "e-mail") and isinstance(v, str):
                ne = norm_email(v)
                if ne:
                    found.add(ne)
            else:
                walk_json(v, found)
    elif isinstance(obj, list):
        for it in obj:
            walk_json(it, found)


def extract_emails(html: str) -> set[str]:
    found: set[str] = set()
    for m in MAILTO_RE.finditer(html):
        ne = norm_email(m.group(1))
        if ne:
            found.add(ne)
    for m in CFEMAIL_RE.finditer(html):
        ne = decode_cfemail(m.group(1))
        if ne:
            found.add(ne)
    for m in OBFUSC_RE.finditer(html):
        ne = norm_email(f"{m.group(1)}@{m.group(2)}.{m.group(3)}")
        if ne:
            found.add(ne)
    for m in LD_JSON.finditer(html):
        try:
            walk_json(json.loads(m.group(1).strip()), found)
        except json.JSONDecodeError:
            pass
    plain = strip_tags(html)
    for m in EMAIL_RE.finditer(plain):
        ne = norm_email(m.group(0))
        if ne:
            found.add(ne)
    for m in EMAIL_RE.finditer(html):
        s = m.group(0)
        if len(s) <= 80:
            ne = norm_email(s)
            if ne:
                found.add(ne)
    return found


def same_host(a: str, b: str) -> bool:
    return urllib.parse.urlsplit(a).netloc.lower().replace("www.", "") == urllib.parse.urlsplit(
        b
    ).netloc.lower().replace("www.", "")


def harvest_links(html: str, base: str, limit: int) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for href in HREF_RE.findall(html):
        href = html_lib.unescape(href.strip())
        if href.startswith("mailto:"):
            continue
        full = urllib.parse.urljoin(base, href)
        if should_skip(full) or not same_host(full, base):
            continue
        low = full.lower()
        if not any(h in low for h in URL_HINTS):
            continue
        if full not in seen:
            seen.add(full)
            out.append(full)
        if len(out) >= limit:
            break
    return out


def _lt(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def sitemap_urls(xml_text: str, base: str, limit: int) -> list[str]:
    urls: list[str] = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return urls
    rt = _lt(root.tag)
    if rt == "sitemapindex":
        for sm in root:
            if _lt(sm.tag) != "sitemap":
                continue
            for ch in sm:
                if _lt(ch.tag) == "loc" and (ch.text or "").strip():
                    urls.append(ch.text.strip())
        return urls[:30]
    if rt == "urlset":
        for el in root:
            if _lt(el.tag) != "url":
                continue
            for ch in el:
                if _lt(ch.tag) == "loc" and (ch.text or "").strip():
                    loc = ch.text.strip()
                    if same_host(loc, base):
                        urls.append(loc)
    prio, rest = [], []
    for u in urls:
        (prio if any(h in u.lower() for h in URL_HINTS) else rest).append(u)
    return (prio + rest)[:limit]


def crawl_domain(
    seed: str,
    fetcher: Fetcher,
    delay: float,
    max_pages: int,
    wall_seconds: float = 0.0,
) -> tuple[set[str], int, str]:
    emails: set[str] = set()
    to_visit: list[str] = []
    for path in CONTACT_PATHS:
        to_visit.append(join_url(seed, path) if path else seed)
    seen: set[str] = set()
    fetched = 0
    last_err = ""
    started = time.monotonic()
    while to_visit and fetched < max_pages:
        if wall_seconds > 0 and (time.monotonic() - started) >= wall_seconds:
            return emails, fetched, "timeout"
        u = to_visit.pop(0)
        if u in seen:
            continue
        seen.add(u)
        time.sleep(delay)
        html, err = fetcher.get(u)
        if not html:
            last_err = err
            continue
        fetched += 1
        emails |= extract_emails(html)
        if fetched == 1 and len(emails) < 3:
            for link in harvest_links(html, u, limit=8):
                if link not in seen and link not in to_visit and len(to_visit) < 20:
                    to_visit.append(link)
        if fetched <= 2 and len(emails) < 2:
            p = urllib.parse.urlsplit(seed)
            origin = urllib.parse.urlunsplit((p.scheme, p.netloc, "/", "", ""))
            for sp in ("/sitemap.xml", "/wp-sitemap.xml"):
                if wall_seconds > 0 and (time.monotonic() - started) >= wall_seconds:
                    break
                time.sleep(delay)
                xml, _ = fetcher.get(join_url(origin, sp))
                if xml and xml.strip().startswith("<"):
                    for su in sitemap_urls(xml, seed, limit=10):
                        if su not in seen and su not in to_visit and len(to_visit) < 20:
                            to_visit.append(su)
    status = "ok" if fetched else ("blocked" if "403" in last_err else "no_html")
    return emails, fetched, status


def _mp_crawl_worker(
    seed: str,
    delay: float,
    max_pages: int,
    wall_seconds: float,
    timeout: float,
    use_cloudscraper: bool,
    out_q: "mp.Queue",
) -> None:
    fetcher = Fetcher(timeout=timeout, use_cloudscraper=use_cloudscraper)
    try:
        em, n, st = crawl_domain(seed, fetcher, delay, max_pages, wall_seconds)
        out_q.put((list(em), n, st))
    except Exception as exc:
        out_q.put(([], 0, f"err:{str(exc)[:120]}"))


def crawl_domain_timed(
    seed: str,
    fetcher: Fetcher,
    delay: float,
    max_pages: int,
    domain_timeout: float,
    *,
    http_timeout: float = 25.0,
    use_cloudscraper: bool = False,
) -> tuple[set[str], int, str]:
    """Corta dominios colgados (subprocess kill; threads no bastan en macOS)."""
    wall = domain_timeout if domain_timeout > 0 else 0.0
    if domain_timeout <= 0:
        return crawl_domain(seed, fetcher, delay, max_pages, wall_seconds=0.0)

    # fork en mac arranca mucho más rápido que spawn (evita “pegado” en [12/154])
    ctx = mp.get_context("fork" if platform.system() == "Darwin" else "spawn")
    q: mp.Queue = ctx.Queue()
    proc = ctx.Process(
        target=_mp_crawl_worker,
        args=(seed, delay, max_pages, wall, http_timeout, use_cloudscraper, q),
    )
    proc.start()
    proc.join(domain_timeout + 15)
    if proc.is_alive():
        proc.terminate()
        proc.join(2)
        if proc.is_alive():
            proc.kill()
        proc.join(1)
        return set(), 0, "timeout"
    if q.empty():
        return set(), 0, "timeout"
    em_list, n, st = q.get()
    return set(em_list), int(n), str(st)


def pick_best(cands: set[str]) -> str | None:
    if not cands:
        return None

    def score(e: str) -> int:
        loc = e.split("@", 1)[0].lower()
        if loc in LOW_LOCAL:
            return 5
        return 50

    return max(cands, key=score)


def read_csv(path: Path, sep: str) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        r = csv.DictReader(f, delimiter=sep)
        fn = list(r.fieldnames or [])
        return fn, [dict(row) for row in r]


LOG_FIELDS = ["domain", "seed_url", "pages_fetched", "emails_found", "status", "sample_emails"]


def load_resume_log(log_path: Path) -> tuple[dict[str, set[str]], list[dict[str, str]]]:
    """Dominios ya procesados en un log previo (para --resume)."""
    domain_emails: dict[str, set[str]] = {}
    log_rows: list[dict[str, str]] = []
    if not log_path.is_file():
        return domain_emails, log_rows
    with log_path.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            dom = (row.get("domain") or "").strip().lower()
            if not dom:
                continue
            emails: set[str] = set()
            for part in (row.get("sample_emails") or "").split(";"):
                ne = norm_email(part.strip())
                if ne:
                    emails.add(ne)
            domain_emails[dom] = emails
            log_rows.append({k: row.get(k, "") for k in LOG_FIELDS})
    return domain_emails, log_rows


def append_log_row(log_path: Path, row: dict[str, str], write_header: bool) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=LOG_FIELDS, extrasaction="ignore")
        if write_header:
            w.writeheader()
        w.writerow(row)


def main() -> int:
    ap = argparse.ArgumentParser(description="Enriquecimiento gratis desde websites.")
    ap.add_argument("input_csv", type=Path)
    ap.add_argument("-o", "--instantly-out", type=Path, required=True)
    ap.add_argument("--enriched-out", type=Path, default=None)
    ap.add_argument("--log-out", type=Path, default=Path("campaign_outputs/enrich_free_log.csv"))
    ap.add_argument("--sep", default=";")
    ap.add_argument("--delay", type=float, default=0.8)
    ap.add_argument("--timeout", type=float, default=25.0)
    ap.add_argument("--max-pages", type=int, default=16)
    ap.add_argument(
        "--cloudscraper",
        action="store_true",
        help="Usar pip install cloudscraper (mejor vs Cloudflare).",
    )
    ap.add_argument(
        "--no-cloudscraper",
        action="store_true",
        help="Forzar urllib (timeouts más fiables; recomendado si se cuelga en [11/154]).",
    )
    ap.add_argument(
        "--resume",
        action="store_true",
        help="Saltar dominios ya en --log-out (log se escribe tras cada dominio).",
    )
    ap.add_argument(
        "--domain-timeout",
        type=float,
        default=90.0,
        help="Segundos máximos por dominio (0 = sin límite).",
    )
    args = ap.parse_args()

    if args.cloudscraper and not HAS_CLOUDSCRAPER:
        print("Instala: pip install cloudscraper", file=sys.stderr)
        return 1

    if not args.input_csv.is_file():
        print(f"No existe {args.input_csv}", file=sys.stderr)
        return 1

    fieldnames, rows = read_csv(args.input_csv, args.sep)
    use_cs = args.cloudscraper and not args.no_cloudscraper
    fetcher = Fetcher(timeout=args.timeout, use_cloudscraper=use_cs)
    if args.no_cloudscraper:
        print("Fetcher: urllib (sin cloudscraper)", file=sys.stderr)

    by_dom: dict[str, str] = {}
    for row in rows:
        w = canonicalize(row.get("website", "") or "")
        if w and not should_skip(w):
            dom = urllib.parse.urlsplit(w).netloc.lower().replace("www.", "")
            if dom and dom not in by_dom:
                by_dom[dom] = w

    domain_emails: dict[str, set[str]] = {}
    log_rows: list[dict[str, str]] = []
    done_domains: set[str] = set()

    if args.resume:
        domain_emails, log_rows = load_resume_log(args.log_out)
        done_domains = set(domain_emails.keys())
        if done_domains:
            print(f"Resume: {len(done_domains)} dominios ya en log, se saltan.", file=sys.stderr)

    if not args.resume and args.log_out.is_file():
        args.log_out.unlink()

    print(f"Dominios a rastrear: {len(by_dom)}", file=sys.stderr)
    sorted_domains = sorted(by_dom.items())
    for i, (dom, seed) in enumerate(sorted_domains, 1):
        if dom in done_domains:
            print(f"  [{i}/{len(by_dom)}] {dom} skip (resume)", file=sys.stderr, flush=True)
            continue
        if dom in HARD_SKIP_DOMAINS:
            row = {
                "domain": dom,
                "seed_url": seed,
                "pages_fetched": "0",
                "emails_found": "0",
                "status": "timeout",
                "sample_emails": "",
            }
            domain_emails[dom] = set()
            log_rows.append(row)
            append_log_row(
                args.log_out,
                row,
                write_header=not args.log_out.exists() or args.log_out.stat().st_size == 0,
            )
            print(f"  [{i}/{len(by_dom)}] {dom} skip (hard_timeout)", file=sys.stderr, flush=True)
            continue
        print(f"  [{i}/{len(by_dom)}] {dom} fetching...", file=sys.stderr, flush=True)
        em, nfetch, status = crawl_domain_timed(
            seed,
            fetcher,
            args.delay,
            args.max_pages,
            args.domain_timeout,
            http_timeout=args.timeout,
            use_cloudscraper=use_cs,
        )
        domain_emails[dom] = em
        row = {
            "domain": dom,
            "seed_url": seed,
            "pages_fetched": str(nfetch),
            "emails_found": str(len(em)),
            "status": status,
            "sample_emails": ";".join(sorted(em)[:5]),
        }
        log_rows.append(row)
        append_log_row(args.log_out, row, write_header=not args.log_out.is_file() or args.log_out.stat().st_size == 0)
        print(f"  [{i}/{len(by_dom)}] {dom} fetch={nfetch} emails={len(em)} {status}", file=sys.stderr)
        sys.stderr.flush()

    for col in ("email_enriched", "enrich_source"):
        if col not in fieldnames:
            fieldnames.append(col)

    instantly: dict[str, dict[str, str]] = {}

    def upsert_inst(email: str, row: dict[str, str], src: str) -> None:
        try:
            sc = int(float(row.get("lead_score") or 0))
        except (TypeError, ValueError):
            sc = 0
        if email not in instantly or sc > int(instantly[email].get("lead_score") or 0):
            instantly[email] = {
                "email": email,
                "company": (row.get("company_name") or "").strip(),
                "website": (row.get("website") or "").strip(),
                "phone": (row.get("phone") or "").strip(),
                "city": (row.get("city") or "").strip(),
                "state": (row.get("state") or "").strip(),
                "country": (row.get("country") or "").strip(),
                "google_maps_url": (row.get("google_maps_url") or "").strip(),
                "lead_score": str(sc),
                "email_source": src,
            }

    for row in rows:
        pool: set[str] = set()
        ne0 = norm_email((row.get("email") or "").strip())
        if ne0:
            pool.add(ne0)
        w = canonicalize(row.get("website", "") or "")
        if w:
            dom = urllib.parse.urlsplit(w).netloc.lower().replace("www.", "")
            pool |= domain_emails.get(dom, set())
        best = pick_best(pool)
        if best:
            row["email_enriched"] = best
            row["enrich_source"] = "csv" if ne0 and best == ne0 else "free_scrape"
            upsert_inst(best, row, row["enrich_source"])
        else:
            row["email_enriched"] = ""
            row["enrich_source"] = ""

    if args.enriched_out:
        args.enriched_out.parent.mkdir(parents=True, exist_ok=True)
        with args.enriched_out.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames, delimiter=args.sep, extrasaction="ignore")
            w.writeheader()
            for row in rows:
                w.writerow({k: row.get(k, "") for k in fieldnames})

    inst_fields = [
        "email",
        "company",
        "website",
        "phone",
        "city",
        "state",
        "country",
        "google_maps_url",
        "lead_score",
        "email_source",
    ]
    args.instantly_out.parent.mkdir(parents=True, exist_ok=True)
    with args.instantly_out.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=inst_fields, extrasaction="ignore")
        w.writeheader()
        for em in sorted(instantly, key=lambda e: (-int(instantly[e].get("lead_score") or 0), e)):
            w.writerow(instantly[em])

    if not args.resume:
        args.log_out.parent.mkdir(parents=True, exist_ok=True)
        with args.log_out.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=LOG_FIELDS)
            w.writeheader()
            w.writerows(log_rows)

    n = sum(1 for r in rows if (r.get("email_enriched") or "").strip())
    print(
        f"\nListo.\n  filas con email: {n}/{len(rows)}\n  únicos Instantly: {len(instantly)}\n"
        f"  -> {args.instantly_out}\n  log -> {args.log_out}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
