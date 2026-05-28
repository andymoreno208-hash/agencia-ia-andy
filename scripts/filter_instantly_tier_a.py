#!/usr/bin/env python3
"""
Tier A para Instantly: dominio email = dominio website, sin blocklist, lead_score mínimo.

Uso:
  python3 scripts/filter_instantly_tier_a.py campaign_outputs/medspa_us_run1_instantly.csv \\
    -o campaign_outputs/medspa_us_run1_instantly_tier_a.csv
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prep_medspa_us_run1 import BLOCKLIST_DOMAIN_SUBSTR, _email_ok  # noqa: E402

MIN_LEAD_SCORE = 50


def email_domain(email: str) -> str:
    return email.split("@", 1)[1].lower().strip()


def website_domain(url: str) -> str:
    if not url or not str(url).strip():
        return ""
    s = str(url).strip()
    if not s.startswith(("http://", "https://")):
        s = "https://" + s
    host = (urlparse(s).hostname or "").lower()
    return host[4:] if host.startswith("www.") else host


def tier_a(df: pd.DataFrame, min_score: int) -> pd.DataFrame:
    work = df.copy()
    work["email"] = work["email"].astype(str).str.strip().str.lower()
    work = work[work["email"].str.contains("@", na=False)]
    work = work[work["email"].map(_email_ok)]

    def domain_match(row: pd.Series) -> bool:
        ed = email_domain(row["email"])
        wd = website_domain(str(row.get("website", "") or ""))
        if not wd:
            return False
        if any(b in ed for b in BLOCKLIST_DOMAIN_SUBSTR):
            return False
        return ed == wd or ed.endswith("." + wd)

    work = work[work.apply(domain_match, axis=1)]

    if "lead_score" in work.columns:
        work["lead_score"] = pd.to_numeric(work["lead_score"], errors="coerce").fillna(0)
        work = work[work["lead_score"] >= min_score]

    work = work.drop_duplicates(subset=["email"], keep="first")
    return work.sort_values(by="lead_score", ascending=False)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("input_csv", type=Path)
    ap.add_argument("-o", "--output", type=Path, required=True)
    ap.add_argument("--min-score", type=int, default=MIN_LEAD_SCORE)
    args = ap.parse_args()

    if not args.input_csv.is_file():
        print(f"No existe {args.input_csv}", file=sys.stderr)
        return 1

    df = pd.read_csv(args.input_csv)
    out = tier_a(df, args.min_score)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.output, index=False)
    print(f"Tier A: {len(df)} -> {len(out)} -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
