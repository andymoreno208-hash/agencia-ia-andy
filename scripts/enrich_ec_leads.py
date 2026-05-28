#!/usr/bin/env python3
"""
Enriquece emails para leads Ecuador (CSV con ';') a partir de la columna website.

Estrategia (por dominio único):
  1) Emails ya presentes en el CSV (se respetan).
  2) API Hunter.io domain-search (opcional): variable de entorno HUNTER_API_KEY o --hunter-key.
  3) Descarga sitemap.xml (y sitemap index) + enlaces en robots.txt → URLs del mismo host
     que parezcan contacto/nosotros/equipo/etc.
  4) Rutas fijas (/contacto, /contact, …) + HTML con extracción mailto / JSON-LD / regex.

Salidas:
  - CSV completo enriquecido (misma estructura + columnas email_enriched, enrich_source)
  - CSV reducido para Instantly (email + company + …)

Uso:
  export HUNTER_API_KEY=xxxxx   # opcional, 25 búsquedas/mes en plan free típico
  python scripts/enrich_ec_leads.py \\
    campaign_outputs/dataset_places_ec_prep.csv \\
    --sep ';' \\
    --enriched-out campaign_outputs/dataset_places_ec_enriched.csv \\
    --instantly-out campaign_outputs/instantly_from_ec_prep.csv \\
    --delay 0.6 --max-fetch-per-domain 22
"""

from __future__ import annotations

import argparse
import csv
import html as html_lib
import json
import os
import re
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

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
)

URL_HINTS = (
    "contact",
    "contacto",
    "nosotros",
    "about",
    "equipo",
    "team",
    "ubicacion",
    "ubicación",
    "cita",
    "ventas",
    "correo",
    "escrib",
)

SKIP_HOST_SUBSTRINGS = (
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
    "google.com/maps",
    "goo.gl",
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
LD_JSON_BLOCK = re.compile(
    r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>',
    re.IGNORECASE | re.DOTALL,
)
JSON_EMAIL_KV = re.compile(
    r'"(?:email|contactEmail|mail|correo|e-mail)"\s*:\s*"([^"]+)"',
    re.IGNORECASE,
)

# Rechazados duros (no importar a Instantly)
BLOCKED_LOCAL = frozenset(
    {
        "noreply",
        "no-reply",
        "donotreply",
        "mailer-daemon",
        "postmaster",
        "webmaster",
        "hostmaster",
        "abuse",
        "privacy",
        "legal",
        "newsletter",
        "news",
        "bounce",
    }
)

# Genéricos aceptables pero con menor prioridad
LOW_PRIORITY_LOCAL = frozenset(
    {
        "info",
        "contact",
        "contacto",
        "ventas",
        "hello",
        "hola",
        "sales",
        "support",
        "soporte",
        "mail",
    }
)

PLACEHOLDER_DOMAINS = frozenset(
    {
        "example.com",
        "test.com",
        "localhost",
        "sentry.io",
        "wixpress.com",
    }
)


def _norm_email(raw: str) -> str | None:
    e = raw.strip().strip('"').strip("'").rstrip(".,);")
    if "@" not in e:
        return None
    el = e.lower()
    if el.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg")):
        return None
    if not EMAIL_RE.fullmatch(el):
        return None
    local, _, domain = el.partition("@")
    if domain in PLACEHOLDER_DOMAINS:
        return None
    if local in BLOCKED_LOCAL:
        return None
    return el


def should_skip_url(url: str) -> bool:
    if not url or not url.startswith(("http://", "https://")):
        return True
    low = url.lower()
    return any(s in low for s in SKIP_HOST_SUBSTRINGS)


def canonicalize_website(raw: str) -> str | None:
    s = (raw or "").strip().strip('"')
    if not s:
        return None
    if s.startswith("//"):
        s = "https:" + s
    if not s.startswith("http"):
        s = "https://" + s
    parts = urllib.parse.urlsplit(s)
    if not parts.netloc:
        return None
    return urllib.parse.urlunsplit(
        (parts.scheme or "https", parts.netloc, parts.path or "/", parts.query, "")
    )


def join_url(base: str, path: str) -> str:
    if not path:
        return base
    return urllib.parse.urljoin(base.rstrip("/") + "/", path.lstrip("/"))


def url_variants(url: str) -> list[str]:
    p = urllib.parse.urlsplit(url)
    scheme, netloc, path, query, fragment = p
    hosts = [netloc]
    if netloc.startswith("www."):
        bare = netloc[4:]
        if bare:
            hosts.append(bare)
    else:
        hosts.append("www." + netloc)
    out: list[str] = []
    seen: set[str] = set()
    for h in hosts:
        for sch in ("https", "http"):
            u = urllib.parse.urlunsplit((sch, h, path or "/", query, fragment))
            if u not in seen:
                seen.add(u)
                out.append(u)
    return out


def fetch_bytes(url: str, timeout: float, ua: str) -> tuple[bytes | None, str | None]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": ua,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "es-EC,es;q=0.9,en;q=0.8",
            "Accept-Encoding": "identity",
            "Connection": "close",
        },
        method="GET",
    )
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            return resp.read(2_500_000), None
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError) as e:
        return None, str(e)[:240]


def fetch_text_first_ok(url: str, timeout: float, ua: str) -> tuple[str | None, str | None]:
    last_err = None
    for u in url_variants(url):
        raw, err = fetch_bytes(u, timeout=timeout, ua=ua)
        if raw:
            try:
                return raw.decode("utf-8", errors="replace"), None
            except Exception:
                return raw.decode("latin-1", errors="replace"), None
        last_err = err
    return None, last_err


def strip_tags(html: str) -> str:
    html = re.sub(r"(?is)<script[^>]*>.*?</script>", " ", html)
    html = re.sub(r"(?is)<style[^>]*>.*?</style>", " ", html)
    html = re.sub(r"(?is)<[^>]+>", " ", html)
    return html_lib.unescape(html)


def _walk_json(obj: object, found: set[str]) -> None:
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k.lower() in ("email", "e-mail") and isinstance(v, str):
                ne = _norm_email(v)
                if ne:
                    found.add(ne)
            else:
                _walk_json(v, found)
    elif isinstance(obj, list):
        for it in obj:
            _walk_json(it, found)


def extract_emails_from_html(html: str) -> set[str]:
    found: set[str] = set()
    for m in MAILTO_RE.finditer(html):
        ne = _norm_email(m.group(1))
        if ne:
            found.add(ne)
    for m in LD_JSON_BLOCK.finditer(html):
        blob = m.group(1).strip()
        if not blob:
            continue
        try:
            data = json.loads(blob)
        except json.JSONDecodeError:
            continue
        _walk_json(data, found)
    for m in JSON_EMAIL_KV.finditer(html):
        ne = _norm_email(m.group(1))
        if ne:
            found.add(ne)
    plain = strip_tags(html)
    for m in EMAIL_RE.finditer(plain):
        ne = _norm_email(m.group(0))
        if ne:
            found.add(ne)
    for m in EMAIL_RE.finditer(html):
        s = m.group(0)
        if len(s) > 80:
            continue
        ne = _norm_email(s)
        if ne:
            found.add(ne)
    return found


def netloc_of(url: str) -> str:
    return urllib.parse.urlsplit(url).netloc.lower()


def same_registrable_domain(a: str, b: str) -> bool:
    return netloc_of(a).replace("www.", "") == netloc_of(b).replace("www.", "")


def _lt(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def parse_sitemap_urls(xml_text: str, base_site: str, limit: int) -> list[str]:
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
            for child in sm:
                if _lt(child.tag) == "loc" and (child.text or "").strip():
                    urls.append(child.text.strip())
        return urls[:50]
    if rt == "urlset":
        for el in root:
            if _lt(el.tag) != "url":
                continue
            loc = None
            for child in el:
                if _lt(child.tag) == "loc" and (child.text or "").strip():
                    loc = child.text.strip()
                    break
            if loc and same_registrable_domain(loc, base_site):
                urls.append(loc)
    return urls[:limit]


def discover_extra_urls(seed: str, ua: str, timeout: float, max_sitemap: int) -> list[str]:
    """Sitemaps + robots Sitemap: + URLs priorizadas por palabras clave."""
    p = urllib.parse.urlsplit(seed)
    origin = urllib.parse.urlunsplit((p.scheme, p.netloc, "/", "", ""))
    collected: list[str] = []
    seen: set[str] = set()

    def add(u: str) -> None:
        u = u.strip()
        if not u or u in seen:
            return
        if should_skip_url(u):
            return
        if not same_registrable_domain(u, seed):
            return
        seen.add(u)
        collected.append(u)

    for path in ("/robots.txt",):
        txt, _ = fetch_text_first_ok(join_url(origin, path), timeout=timeout, ua=ua)
        if not txt:
            continue
        for line in txt.splitlines():
            low = line.lower().strip()
            if low.startswith("sitemap:"):
                add(low.split(":", 1)[1].strip())

    sm_urls: list[str] = []
    for path in ("/sitemap.xml", "/sitemap_index.xml", "/wp-sitemap.xml", "/sitemap_index.xml"):
        xmlt, _ = fetch_text_first_ok(join_url(origin, path), timeout=timeout, ua=ua)
        if not xmlt or not xmlt.strip().startswith("<"):
            continue
        if "sitemapindex" in xmlt.lower()[:400]:
            child_maps = parse_sitemap_urls(xmlt, seed, limit=30)
            for cm in child_maps:
                t2, _ = fetch_text_first_ok(cm, timeout=timeout, ua=ua)
                if t2 and t2.strip().startswith("<"):
                    sm_urls.extend(parse_sitemap_urls(t2, seed, limit=max_sitemap))
        else:
            sm_urls.extend(parse_sitemap_urls(xmlt, seed, limit=max_sitemap))

    prioritized: list[str] = []
    rest: list[str] = []
    for u in sm_urls:
        lu = u.lower()
        if any(h in lu for h in URL_HINTS):
            prioritized.append(u)
        else:
            rest.append(u)
    out = prioritized + rest
    return out[:max_sitemap]


def hunter_domain_emails(domain: str, api_key: str, timeout: float) -> set[str]:
    out: set[str] = set()
    if not api_key or not domain:
        return out
    q = urllib.parse.urlencode({"domain": domain, "api_key": api_key, "limit": "15"})
    url = "https://api.hunter.io/v2/domain-search?" + q
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read(500_000)
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError):
        return out
    try:
        data = json.loads(raw.decode("utf-8", errors="replace"))
    except json.JSONDecodeError:
        return out
    emails = (data.get("data") or {}).get("emails") or []
    for item in emails:
        val = (item.get("value") or "").strip()
        ne = _norm_email(val)
        if ne:
            out.add(ne)
    return out


def email_score(email: str) -> int:
    local = email.split("@", 1)[0].lower()
    if local in BLOCKED_LOCAL:
        return -100
    if local in LOW_PRIORITY_LOCAL or any(x in local for x in ("ventas", "info", "contact", "hello", "hola")):
        return 10
    return 50


def pick_best_email(candidates: set[str]) -> tuple[str | None, str]:
    if not candidates:
        return None, ""
    best = max(candidates, key=lambda e: (email_score(e), len(e)))
    return best, "scored"


def read_rows(path: Path, sep: str) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        r = csv.DictReader(f, delimiter=sep)
        fields = list(r.fieldnames or [])
        return fields, [dict(row) for row in r]


def score_row(row: dict[str, str]) -> int:
    try:
        return int(float(row.get("lead_score") or 0))
    except (TypeError, ValueError):
        return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Enriquece emails desde websites (EC prep CSV).")
    ap.add_argument("input_csv", type=Path)
    ap.add_argument("--sep", default=";")
    ap.add_argument(
        "--enriched-out",
        type=Path,
        default=Path("campaign_outputs/dataset_places_ec_enriched.csv"),
    )
    ap.add_argument(
        "--instantly-out",
        type=Path,
        default=Path("campaign_outputs/instantly_from_ec_prep.csv"),
    )
    ap.add_argument("--delay", type=float, default=0.7)
    ap.add_argument("--timeout", type=float, default=22.0)
    ap.add_argument("--max-fetch-per-domain", type=int, default=22)
    ap.add_argument("--max-sitemap-urls", type=int, default=80)
    ap.add_argument(
        "--hunter-key",
        default=os.environ.get("HUNTER_API_KEY", ""),
        help="API key Hunter (o env HUNTER_API_KEY).",
    )
    ap.add_argument("--dry-run", action="store_true", help="No HTTP (solo CSV merge).")
    args = ap.parse_args()

    if not args.input_csv.is_file():
        print(f"No existe {args.input_csv}", file=sys.stderr)
        return 1

    fieldnames, rows = read_rows(args.input_csv, args.sep)
    ua = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    )

    # dominio -> set emails
    domain_to_urls: dict[str, str] = {}
    for row in rows:
        w = canonicalize_website(row.get("website", "") or "")
        if not w or should_skip_url(w):
            continue
        dom = netloc_of(w).replace("www.", "")
        if dom and dom not in domain_to_urls:
            domain_to_urls[dom] = w

    domain_emails: dict[str, set[str]] = {d: set() for d in domain_to_urls}

    # Hunter primero (barato en requests)
    hk = (args.hunter_key or "").strip()
    if hk and not args.dry_run:
        print(f"Hunter: {len(domain_to_urls)} dominios…", file=sys.stderr)
        for i, dom in enumerate(sorted(domain_to_urls), 1):
            time.sleep(args.delay)
            found = hunter_domain_emails(dom, hk, timeout=args.timeout)
            domain_emails[dom] |= found
            print(f"  [{i}/{len(domain_to_urls)}] {dom} hunter -> {len(found)}", file=sys.stderr)

    if not args.dry_run:
        print("Crawl web + sitemaps…", file=sys.stderr)
        for i, (dom, seed) in enumerate(sorted(domain_to_urls.items()), 1):
            to_fetch: list[str] = []
            for path in CONTACT_PATHS:
                to_fetch.append(join_url(seed, path) if path else seed)
            try:
                extra = discover_extra_urls(seed, ua=ua, timeout=args.timeout, max_sitemap=args.max_sitemap_urls)
            except Exception:
                extra = []
            for u in extra:
                if u not in to_fetch:
                    to_fetch.append(u)
            seen_u: set[str] = set()
            fetched = 0
            for u in to_fetch:
                if fetched >= args.max_fetch_per_domain:
                    break
                if u in seen_u:
                    continue
                seen_u.add(u)
                time.sleep(args.delay)
                html, err = fetch_text_first_ok(u, timeout=args.timeout, ua=ua)
                if not html:
                    continue
                fetched += 1
                domain_emails[dom] |= extract_emails_from_html(html)
            print(
                f"  [{i}/{len(domain_to_urls)}] {dom} crawl -> "
                f"{len(domain_emails[dom])} acumulados (fetch {fetched})",
                file=sys.stderr,
            )

    # fusionar por fila
    extra_cols = ["email_enriched", "enrich_source"]
    for fn in extra_cols:
        if fn not in fieldnames:
            fieldnames.append(fn)

    instantly_rows: dict[str, dict[str, str]] = {}

    def upsert_instantly(email: str, row: dict[str, str], source: str) -> None:
        sc = score_row(row)
        prev = instantly_rows.get(email)
        if prev is None or sc > int(prev.get("lead_score") or 0):
            instantly_rows[email] = {
                "email": email,
                "company": (row.get("company_name") or "").strip(),
                "website": (row.get("website") or "").strip(),
                "phone": (row.get("phone") or "").strip(),
                "city": (row.get("city") or "").strip(),
                "state": (row.get("state") or "").strip(),
                "country": (row.get("country") or "").strip(),
                "google_maps_url": (row.get("google_maps_url") or "").strip(),
                "lead_score": str(sc),
                "email_source": source,
            }

    for row in rows:
        raw_email = (row.get("email") or "").strip()
        ne0 = _norm_email(raw_email) if raw_email else None
        w = canonicalize_website(row.get("website", "") or "")
        dom = netloc_of(w).replace("www.", "") if w else ""
        pool: set[str] = set()
        source_bits: list[str] = []
        if ne0:
            pool.add(ne0)
            source_bits.append("csv")
        if dom and dom in domain_emails:
            pool |= domain_emails[dom]
            if domain_emails[dom] - ({ne0} if ne0 else set()):
                source_bits.append("web" if not hk else "web+hunter")
        best, _ = pick_best_email(pool)
        if best:
            row["email_enriched"] = best
            if ne0 and best == ne0:
                row["enrich_source"] = "csv"
            else:
                row["enrich_source"] = "+".join(sorted(set(source_bits)) or ["web"])
            upsert_instantly(best, row, row["enrich_source"])
        else:
            row["email_enriched"] = ""
            row["enrich_source"] = ""

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
        for em in sorted(
            instantly_rows,
            key=lambda e: (-int(instantly_rows[e].get("lead_score") or 0), e),
        ):
            w.writerow(instantly_rows[em])

    n_with = sum(1 for r in rows if (r.get("email_enriched") or "").strip())
    print(
        f"Listo.\n"
        f"  filas: {len(rows)}\n"
        f"  con email_enriched: {n_with}\n"
        f"  únicos Instantly: {len(instantly_rows)}\n"
        f"  -> {args.enriched_out}\n"
        f"  -> {args.instantly_out}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
