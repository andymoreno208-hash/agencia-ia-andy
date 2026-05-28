#!/usr/bin/env python3
"""
Dedupe + agency filter for Indeed → school research (Upwork M1).

Input: CSV from Apify Indeed actor or manual export (flexible column names).
Output: deduped rows + duplicates report for manual QA.

Example:
  python3 scripts/indeed_schools_dedupe.py \\
    campaign_outputs/indeed_spanish_raw.csv \\
    -o campaign_outputs/indeed_spanish_deduped.csv \\
    --dupes campaign_outputs/indeed_spanish_dupes.csv
"""

from __future__ import annotations

import argparse
import csv
import re
import unicodedata
from pathlib import Path

# Employer / title hints — not schools (client exclusions)
AGENCY_PATTERNS = re.compile(
    r"\b("
    r"staffing|recruit|recruiting|consulting|tutor|tutoring|"
    r"language\s+learning\s+network|\blnn\b|placement|"
    r"workforce|temp\s+agency|substitute\s+staffing|"
    r"ed(?:ucation)?\s+services?\s+inc|charter\s+staffing"
    r")\b",
    re.IGNORECASE,
)

SCHOOL_HINTS = re.compile(
    r"\b("
    r"school|district|isd|usd|csd|academy|charter|"
    r"diocese|catholic|unified|public\s+schools|"
    r"independent\s+school|montessori|prep\s+school"
    r")\b",
    re.IGNORECASE,
)

COL_ALIASES: dict[str, tuple[str, ...]] = {
    "indeed_url": ("indeed_url", "job_url", "url", "link", "indeed link"),
    "job_title": ("job_title", "title", "position"),
    "employer": ("employer", "company", "company_name", "hiring_organization"),
    "district": ("district", "district_name", "district name"),
    "school": ("school", "school_name", "school name"),
    "state": ("state", "state_code", "region"),
    "city": ("city", "location", "metro"),
    "date_posted": ("date_posted", "posted", "date"),
    "search_city": ("search_city", "assigned_city", "query_city"),
}


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def _pick(row: dict[str, str], key: str) -> str:
    aliases = COL_ALIASES[key]
    lower_map = {k.lower().strip(): v for k, v in row.items()}
    for a in aliases:
        if a in lower_map and (lower_map[a] or "").strip():
            return lower_map[a].strip()
    return ""


def _master_key(row: dict[str, str]) -> str:
    district = _norm(_pick(row, "district") or _pick(row, "employer"))
    school = _norm(_pick(row, "school"))
    state = _norm(_pick(row, "state"))
    if school:
        return f"{district}|{school}|{state}"
    return f"{district}|{state}"


def _job_key(row: dict[str, str]) -> str:
    url = (_pick(row, "indeed_url") or "").split("?")[0].strip()
    if url:
        return url
    title = _norm(_pick(row, "job_title"))
    employer = _norm(_pick(row, "employer"))
    return f"{employer}|{title}"


def is_agency(row: dict[str, str]) -> bool:
    blob = " ".join(
        [
            _pick(row, "employer"),
            _pick(row, "district"),
            _pick(row, "school"),
            _pick(row, "job_title"),
        ]
    )
    if AGENCY_PATTERNS.search(blob):
        return True
    # Employer with no school signal and generic name
    employer = _pick(row, "employer")
    if employer and not SCHOOL_HINTS.search(blob) and len(employer.split()) <= 4:
        if not re.search(r"\b(isd|usd|school|district)\b", employer, re.I):
            return False  # let manual QA decide
    return False


def dedupe_rows(rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    kept: list[dict[str, str]] = []
    dupes: list[dict[str, str]] = []
    seen_master: dict[str, int] = {}
    seen_job: set[str] = set()

    for row in rows:
        if is_agency(row):
            row = {**row, "filter_flag": "agency_candidate"}
        jk = _job_key(row)
        if jk in seen_job:
            dupes.append({**row, "dupe_reason": "duplicate_job_url"})
            continue
        mk = _master_key(row)
        if mk in seen_master:
            dupes.append({**row, "dupe_reason": "duplicate_district_school", "canonical_row": str(seen_master[mk])})
            continue
        seen_job.add(jk)
        seen_master[mk] = len(kept) + 2  # 1-based sheet row hint (header + index)
        kept.append(row)

    return kept, dupes


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8-sig")
        return
    if fieldnames is None:
        keys: list[str] = []
        seen: set[str] = set()
        for r in rows:
            for k in r:
                if k not in seen:
                    seen.add(k)
                    keys.append(k)
        fieldnames = keys
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    p = argparse.ArgumentParser(description="Dedupe Indeed school research CSV")
    p.add_argument("input_csv", type=Path)
    p.add_argument("-o", "--output", type=Path, required=True)
    p.add_argument("--dupes", type=Path, default=None, help="Write removed duplicates here")
    args = p.parse_args()

    rows = read_csv(args.input_csv)
    kept, dupes = dedupe_rows(rows)
    write_csv(args.output, kept)
    if args.dupes:
        write_csv(args.dupes, dupes)
    print(f"Input: {len(rows)} | Kept: {len(kept)} | Dupes/agency flags: {len(dupes)}")


if __name__ == "__main__":
    main()
