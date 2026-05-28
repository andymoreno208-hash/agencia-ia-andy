#!/usr/bin/env python3
"""
Enriquece charles_pilot_20_dallas.csv:
  - Email (crawl web, reutiliza enrich_emails_free)
  - Branch_Location_Count (web: /locations, JSON-LD, regex "N locations")

Ejecutar en tu Mac (WiFi):
  python3 scripts/charles_enrich_pilot.py \\
    campaign_outputs/charles_pilot_20_dallas.csv \\
    -o campaign_outputs/charles_pilot_20_dallas_enriched.csv \\
    --cloudscraper --delay 0.8
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
from pathlib import Path
from urllib.parse import urljoin

# Reutilizar crawler probado en EC/MedSpa
sys.path.insert(0, str(Path(__file__).resolve().parent))
from enrich_emails_free import (  # noqa: E402
    Fetcher,
    canonicalize,
    crawl_domain_timed,
    pick_best,
    should_skip,
)
from urllib.parse import urlsplit

LOG_FIELDS = [
    "domain",
    "seed_url",
    "email",
    "email_status",
    "branch_count",
    "branch_method",
    "branch_confidence",
]


def append_charles_log(log_path: Path, row: dict[str, str], write_header: bool) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=LOG_FIELDS, extrasaction="ignore")
        if write_header:
            w.writeheader()
        w.writerow({k: row.get(k, "") for k in LOG_FIELDS})

LOCATION_PATHS = (
    "/locations",
    "/location",
    "/find-a-location",
    "/find-locations",
    "/store-locator",
    "/stores",
    "/our-locations",
    "/franchise",
    "/franchising",
    "/branches",
    "/where-to-buy",
    "/contact/locations",
)

COUNT_TEXT_RE = re.compile(
    r"(\d{1,4})\+?\s*(?:locations?|stores?|restaurants?|offices?|"
    r"franchises?|branches?|units?|sites?)\b",
    re.IGNORECASE,
)
ZIP_RE = re.compile(r"\b(\d{5})(?:-\d{4})?\b")
LOCATION_HREF_RE = re.compile(
    r'href=["\']([^"\']*(?:/locations?/|/stores?/|store-locator)[^"\']*)["\']',
    re.IGNORECASE,
)


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader.fieldnames or []), list(reader)


def walk_json_ld(obj: object, businesses: list[dict]) -> None:
    if isinstance(obj, dict):
        t = obj.get("@type")
        types = [t] if isinstance(t, str) else (t if isinstance(t, list) else [])
        if any(
            x in ("LocalBusiness", "Store", "Restaurant", "Organization", "Place")
            for x in types
        ):
            businesses.append(obj)
        for v in obj.values():
            walk_json_ld(v, businesses)
    elif isinstance(obj, list):
        for x in obj:
            walk_json_ld(x, businesses)


def parse_json_ld_blocks(html: str) -> list[dict]:
    out: list[dict] = []
    for m in re.finditer(
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html,
        re.DOTALL | re.IGNORECASE,
    ):
        raw = m.group(1).strip()
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        walk_json_ld(data, out)
    return out


def estimate_branches_from_html(html: str) -> tuple[str, str, str]:
    """Returns (count_str, method, confidence)."""
    if not html or len(html) < 200:
        return "", "web_fetch_failed", "low"

    businesses = parse_json_ld_blocks(html)
    if len(businesses) >= 2:
        return str(len(businesses)), "json_ld_localbusiness_count", "medium"

    m = COUNT_TEXT_RE.search(html)
    if m:
        n = int(m.group(1))
        if 2 <= n <= 5000:
            return str(n), "regex_locations_phrase_on_page", "medium"

    hrefs = LOCATION_HREF_RE.findall(html)
    unique_hrefs = {h.split("?")[0].rstrip("/") for h in hrefs if h}
    if len(unique_hrefs) >= 3:
        return str(len(unique_hrefs)), "location_page_link_count", "low"

    zips = set(ZIP_RE.findall(html))
    if len(zips) >= 5:
        return str(len(zips)), "unique_zip_codes_on_page", "low"

    return "", "not_found_on_website", "low"


def fetch_page(fetcher: Fetcher, url: str) -> str:
    html, _ = fetcher.get(url)
    return html or ""


def enrich_branches(
    seed_url: str,
    fetcher: Fetcher,
    delay: float,
) -> tuple[str, str, str]:
    base = canonicalize(seed_url)
    if not base or should_skip(base):
        return "", "skip_host", "low"

    pages: list[str] = []
    home = fetch_page(fetcher, base)
    if home:
        pages.append(home)
    time.sleep(delay)

    for path in LOCATION_PATHS:
        u = urljoin(base.rstrip("/") + "/", path.lstrip("/"))
        html = fetch_page(fetcher, u)
        if html and len(html) > 800:
            pages.append(html)
            break
        time.sleep(delay * 0.5)

    best_n = 0
    best_method = "not_found_on_website"
    best_conf = "low"
    for html in pages:
        n_s, method, conf = estimate_branches_from_html(html)
        if not n_s:
            continue
        try:
            n = int(n_s)
        except ValueError:
            continue
        if n > best_n:
            best_n = n
            best_method = method
            best_conf = conf

    if best_n >= 2:
        return str(best_n), best_method, best_conf
    return "1", "maps_hq_only_single_listing", "low"


def domain_key(url: str) -> str:
    w = canonicalize(url)
    if not w:
        return ""
    return urlsplit(w).netloc.lower().replace("www.", "")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("input_csv", type=Path)
    ap.add_argument("-o", "--output", type=Path, required=True)
    ap.add_argument(
        "--top-out",
        type=Path,
        default=None,
        help="CSV con mejores filas (tienen email), ordenadas por branch_count y reviews.",
    )
    ap.add_argument("--top-limit", type=int, default=20)
    ap.add_argument(
        "--log-out",
        type=Path,
        default=Path("campaign_outputs/charles_enrich_60_log.csv"),
    )
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--delay", type=float, default=0.8)
    ap.add_argument("--timeout", type=float, default=25.0)
    ap.add_argument("--domain-timeout", type=float, default=90.0)
    ap.add_argument("--max-pages", type=int, default=12)
    ap.add_argument("--cloudscraper", action="store_true")
    ap.add_argument(
        "--no-cloudscraper",
        action="store_true",
        help="urllib directo (menos cuelgues en corporates).",
    )
    ap.add_argument("--skip-branches", action="store_true")
    ap.add_argument(
        "--emails-only",
        action="store_true",
        help="Solo re-crawlear email; conserva branch del log.",
    )
    ap.add_argument("--skip-emails", action="store_true")
    args = ap.parse_args()

    if not args.input_csv.is_file():
        print(f"No existe {args.input_csv}", file=sys.stderr)
        return 1

    fieldnames, rows = read_csv(args.input_csv)
    use_cs = args.cloudscraper and not args.no_cloudscraper
    fetcher = Fetcher(timeout=args.timeout, use_cloudscraper=use_cs)

    domain_cache: dict[str, dict[str, str]] = {}
    branch_cache: dict[str, dict[str, str]] = {}
    if args.resume and args.log_out.is_file():
        with args.log_out.open("r", encoding="utf-8-sig", newline="") as f:
            for lr in csv.DictReader(f):
                dom = (lr.get("domain") or "").strip().lower()
                if not dom or "@" in dom:
                    continue
                if (lr.get("branch_count") or "").strip():
                    branch_cache[dom] = lr
                if (lr.get("email") or "").strip():
                    domain_cache[dom] = lr
        if domain_cache or branch_cache:
            print(
                f"Resume: {len(domain_cache)} con email, {len(branch_cache)} con branch en log",
                file=sys.stderr,
            )

    if not args.resume and args.log_out.is_file():
        args.log_out.unlink()

    unique_domains: dict[str, str] = {}
    for row in rows:
        site = (row.get("Website") or row.get("website") or "").strip()
        dom = domain_key(site)
        if dom and dom not in unique_domains:
            unique_domains[dom] = site

    print(f"Dominios únicos a enriquecer: {len(unique_domains)}", file=sys.stderr)

    for di, (dom, seed) in enumerate(sorted(unique_domains.items()), 1):
        cached = domain_cache.get(dom)
        branch_prev = branch_cache.get(dom)
        if cached and (cached.get("email") or "").strip():
            print(f"  [{di}/{len(unique_domains)}] {dom} skip (resume, tiene email)", file=sys.stderr, flush=True)
            continue
        if args.emails_only and branch_prev:
            pass  # reintentar email; branch desde branch_cache
        elif cached and not args.emails_only and (cached.get("email") or branch_prev):
            print(f"  [{di}/{len(unique_domains)}] {dom} skip (resume)", file=sys.stderr, flush=True)
            continue
        print(f"  [{di}/{len(unique_domains)}] {dom} ...", file=sys.stderr, flush=True)
        best_email = ""
        email_status = "not_found"
        branch_count = "1"
        branch_method = "maps_hq_only_single_listing"
        branch_conf = "low"

        if not args.skip_emails:
            em, _, status = crawl_domain_timed(
                seed,
                fetcher,
                args.delay,
                args.max_pages,
                args.domain_timeout,
                http_timeout=args.timeout,
                use_cloudscraper=use_cs,
            )
            best = pick_best(em)
            if best:
                best_email = best
                email_status = status or "ok"
            else:
                email_status = status or "not_found"

        if not args.skip_branches and not (args.emails_only and branch_prev):
            branch_count, branch_method, branch_conf = enrich_branches(seed, fetcher, args.delay)
        elif args.emails_only and branch_prev:
            branch_count = branch_prev.get("branch_count") or branch_count
            branch_method = branch_prev.get("branch_method") or branch_method
            branch_conf = branch_prev.get("branch_confidence") or branch_conf

        log_row = {
            "domain": dom,
            "seed_url": seed,
            "email": best_email,
            "email_status": email_status,
            "branch_count": branch_count,
            "branch_method": branch_method,
            "branch_confidence": branch_conf,
        }
        domain_cache[dom] = log_row
        append_charles_log(
            args.log_out,
            log_row,
            write_header=not args.log_out.exists() or args.log_out.stat().st_size == 0,
        )
        time.sleep(args.delay * 0.3)

    for i, row in enumerate(rows, 1):
        site = (row.get("Website") or row.get("website") or "").strip()
        dom = domain_key(site)
        cached = domain_cache.get(dom, {})
        if cached.get("email"):
            row["Email"] = cached["email"]
            row["Email_Source"] = f"free_scrape_{cached.get('email_status', 'ok')}"
        else:
            row["Email"] = row.get("Email") or ""
            row["Email_Source"] = row.get("Email_Source") or "not_found"
        if cached.get("branch_count"):
            row["Branch_Location_Count"] = cached["branch_count"]
            row["Branch_Count_Method"] = cached.get("branch_method", "")
            row["Branch_Count_Confidence"] = cached.get("branch_confidence", "low")
            method = cached.get("branch_method", "")
            if method == "maps_hq_only_single_listing":
                row["Branch_Count_Note"] = (
                    "Solo 1 pin en scrape Dallas. Para conteo TX/franquicia real: "
                    "2º run Apify por nombre de marca en Texas."
                )
            else:
                row["Branch_Count_Note"] = f"Estimado desde web ({method}); validar en muestra."

    extra = ["Email_Source", "Branch_Count_Confidence"]
    for c in extra:
        if c not in fieldnames:
            fieldnames.append(c)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fieldnames})

    n_em = sum(1 for r in rows if (r.get("Email") or "").strip())
    n_br = sum(1 for r in rows if int(r.get("Branch_Location_Count") or "0") > 1)
    print(
        f"\nListo -> {args.output}\n"
        f"  emails: {n_em}/{len(rows)}\n"
        f"  branch_count > 1: {n_br}/{len(rows)}",
        file=sys.stderr,
    )

    if args.top_out:
        with_email = [r for r in rows if (r.get("Email") or "").strip()]

        def top_key(r: dict[str, str]) -> tuple:
            try:
                br = int(r.get("Branch_Location_Count") or 0)
            except ValueError:
                br = 0
            has_em = 1 if (r.get("Email") or "").strip() else 0
            return (-has_em, -br, r.get("Company_Name", ""))

        pool = with_email if with_email else rows
        top = sorted(pool, key=top_key)[: args.top_limit]
        args.top_out.parent.mkdir(parents=True, exist_ok=True)
        with args.top_out.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            w.writeheader()
            for row in top:
                w.writerow({k: row.get(k, "") for k in fieldnames})
        print(f"  top con email ({len(top)}): {args.top_out}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
