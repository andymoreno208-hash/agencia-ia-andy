#!/usr/bin/env python3
"""
Convierte export Apify (Google Maps) en piloto formato Charles (~20 filas).

- Filtra corporate / holding / headquarters en título o categoría
- Excluye gobierno, USPS, coworking (hq.com), filas sin web
- Agrupa por dominio: branch_count_in_scrape = # listings mismo dominio en este CSV
  (con 1 run en Dallas, casi siempre = 1; sube si mezclas más condados/runs)

Uso:
  python3 scripts/charles_pilot_from_apify_maps.py \\
    /Users/andymoreno/Downloads/dataset_crawler-google-places_2026-05-16_16-19-52-917.csv \\
    -o campaign_outputs/charles_pilot_20_dallas.csv \\
    --limit 20
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlparse

CORPORATE_HINTS = (
    "corporate",
    "headquarters",
    "holding",
    "regional office",
    "home office",
    "support center",
    "global headquarters",
)

SKIP_DOMAIN = (
    "usps.com",
    "ssa.gov",
    "va.gov",
    "epa.gov",
    "uspto.gov",
    "hq.com",
    "google.com",
    "commercialcafe.com",
)

SKIP_TITLE = (
    "social security",
    "veterans affairs",
    "patent and trademark",
    "post office",
    "high school",
    "painting & remodeling",
    "narcotics anonymous",
)


def domain_from_url(raw: str) -> str:
    s = (raw or "").strip()
    if not s:
        return ""
    if not s.startswith("http"):
        s = "https://" + s
    try:
        host = urlparse(s).netloc.lower()
    except Exception:
        return ""
    if host.startswith("www."):
        host = host[4:]
    return host


def clean_company(title: str) -> str:
    t = (title or "").strip()
    t = re.sub(r"\s*-\s*Corporate Office\s*$", "", t, flags=re.I)
    t = re.sub(r"\s+Corporate Office\s*$", "", t, flags=re.I)
    t = re.sub(r"\s+Home Office\s*$", "", t, flags=re.I)
    t = re.sub(r"\s+Global Headquarters\s*$", "", t, flags=re.I)
    t = re.sub(r"\s+Corporate Headquarters\s*$", "", t, flags=re.I)
    return t.strip()


def is_corporate_row(row: dict[str, str]) -> bool:
    title = (row.get("title") or "").lower()
    cat = (row.get("categoryName") or "").lower()
    c0 = (row.get("categories/0") or "").lower()
    blob = f"{title} {cat} {c0}"
    if any(x in blob for x in SKIP_TITLE):
        return False
    dom = domain_from_url(row.get("website") or "")
    if dom and any(dom.endswith(d) or dom == d for d in SKIP_DOMAIN):
        return False
    return any(h in blob for h in CORPORATE_HINTS)


def score_row(row: dict[str, str]) -> int:
    sc = 0
    title = (row.get("title") or "").lower()
    if "headquarters" in title or "holding" in title:
        sc += 40
    if "corporate office" in title or "corporate" in (row.get("categories/0") or "").lower():
        sc += 30
    if row.get("website"):
        sc += 20
    try:
        sc += min(int(float(row.get("reviewsCount") or 0)), 50)
    except (TypeError, ValueError):
        pass
    if (row.get("state") or "").lower() in ("texas", "tx"):
        sc += 10
    city = (row.get("city") or "").lower()
    if city in ("dallas", "addison", "plano", "frisco", "irving", "garland", "fort worth"):
        sc += 5
    return sc


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("input_csv", type=Path)
    ap.add_argument("-o", "--output", type=Path, required=True)
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument(
        "--all-rows",
        action="store_true",
        help="Exportar todas las filas con web (sin filtro corporate ni dedupe).",
    )
    ap.add_argument("--county", default="Dallas")
    args = ap.parse_args()

    if not args.input_csv.is_file():
        print(f"No existe {args.input_csv}", file=sys.stderr)
        return 1

    rows = read_csv(args.input_csv)
    by_domain: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        dom = domain_from_url(row.get("website") or "")
        if dom:
            by_domain[dom].append(row)

    candidates: list[dict[str, str]] = []
    for row in rows:
        if not args.all_rows:
            if not is_corporate_row(row):
                continue
            if not (row.get("website") or "").strip():
                continue
        elif not (row.get("website") or "").strip():
            continue
        dom = domain_from_url(row.get("website") or "")
        branch_n = len(by_domain.get(dom, [row])) if dom else 1
        out = {
            "Company_Name": clean_company(row.get("title") or ""),
            "Decision_Maker_Name": "",
            "Title": "",
            "Email": "",
            "Phone": (row.get("phone") or "").strip(),
            "Address": (row.get("street") or "").strip(),
            "Zip": "",
            "City": (row.get("city") or "").strip(),
            "State": (row.get("state") or "Texas").strip(),
            "County": args.county,
            "Website": (row.get("website") or "").strip(),
            "Branch_Location_Count": str(branch_n),
            "Branch_Count_Method": "maps_listings_same_domain_in_this_export",
            "Branch_Count_Note": (
                "Count from this Apify export only. For true TX-wide branch totals, "
                "run a second Maps search per brand."
            ),
            "Source_URL": (row.get("url") or row.get("website") or "").strip(),
            "Maps_Category": (row.get("categoryName") or "").strip(),
            "_score": str(score_row(row)),
        }
        candidates.append(out)

    candidates.sort(key=lambda r: int(r.get("_score") or 0), reverse=True)
    if args.all_rows:
        picked = candidates
    else:
        seen_dom: set[str] = set()
        picked = []
        for row in candidates:
            dom = domain_from_url(row.get("Website") or "")
            if dom and dom in seen_dom:
                continue
            if dom:
                seen_dom.add(dom)
            picked.append(row)
            if len(picked) >= args.limit:
                break

    fields = [
        "Company_Name",
        "Decision_Maker_Name",
        "Title",
        "Email",
        "Phone",
        "Address",
        "Zip",
        "City",
        "State",
        "County",
        "Website",
        "Branch_Location_Count",
        "Branch_Count_Method",
        "Branch_Count_Note",
        "Source_URL",
        "Maps_Category",
    ]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for row in picked:
            w.writerow({k: row.get(k, "") for k in fields})

    print(
        f"Input rows: {len(rows)}\n"
        f"Corporate candidates: {len(candidates)}\n"
        f"Pilot exported: {len(picked)}\n"
        f"-> {args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
