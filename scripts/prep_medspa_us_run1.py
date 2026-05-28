#!/usr/bin/env python3
"""
Prep Run 1: dedupe Apify Google Maps export + filtros de calidad (plan MedSpa US).

Uso:
  python3 scripts/prep_medspa_us_run1.py campaign_outputs/medspa_us_run1_apify.csv \\
    -o campaign_outputs/medspa_us_run1_prep.csv
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd

MIN_REVIEWS = 15
MIN_SCORE = 4.0

BLOCKLIST_DOMAIN_SUBSTR = (
    "wixpress.com",
    "sentry.io",
    "wix.com",
    "mysite.com",
    "hostingersite.com",
    "latofonts.com",
    "indiantypefoundry.com",
    "greensock.com",
    "vagaro.com",
    "healthprofs.com",
    "sentry-next",
    "example.com",
    "test.com",
)

BLOCKLIST_LOCAL = frozenset(
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

ASSET_LOCAL_RE = re.compile(r"\.(png|jpg|jpeg|gif|webp|svg|ico)$", re.I)


def _col(df: pd.DataFrame, *names: str) -> str | None:
    lower = {c.lower(): c for c in df.columns}
    for n in names:
        if n.lower() in lower:
            return lower[n.lower()]
    return None


def _domain(url: object) -> str:
    if pd.isna(url) or not str(url).strip():
        return ""
    s = str(url).strip()
    if not s.startswith(("http://", "https://")):
        s = "https://" + s
    host = (urlparse(s).hostname or "").lower()
    return host[4:] if host.startswith("www.") else host


def _email_ok(email: object) -> bool:
    if pd.isna(email) or not str(email).strip():
        return True
    e = str(email).strip().lower()
    if "@" not in e:
        return False
    local, _, dom = e.partition("@")
    if local in BLOCKLIST_LOCAL:
        return False
    if ASSET_LOCAL_RE.search(local):
        return False
    if any(b in dom for b in BLOCKLIST_DOMAIN_SUBSTR):
        return False
    return True


def score_row(row: pd.Series) -> int:
    score = 0
    ws = str(row.get("website", "") or "").strip()
    if ws:
        score += 20
    em = str(row.get("email", "") or "").strip()
    if em and "@" in em:
        score += 25
        ed = em.split("@", 1)[1]
        wd = _domain(ws)
        if wd and ed == wd:
            score += 30
    try:
        rc = float(row.get("reviewsCount") or 0)
        if rc >= MIN_REVIEWS:
            score += 15
        if rc >= 50:
            score += 5
    except (TypeError, ValueError):
        pass
    try:
        ts = float(row.get("totalScore") or 0)
        if ts >= 4.5:
            score += 10
    except (TypeError, ValueError):
        pass
    ph = row.get("phone")
    if pd.notna(ph) and str(ph).strip():
        score += 5
    return score


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    rename = {}
    if "title" in df.columns and "company_name" not in df.columns:
        rename["title"] = "company_name"
    url_col = _col(df, "url", "googleMapsUrl", "google_maps_url")
    if url_col and url_col != "google_maps_url":
        rename[url_col] = "google_maps_url"
    place_col = _col(df, "placeId", "place_id")
    if place_col and place_col != "placeId":
        rename[place_col] = "placeId"
    cc = _col(df, "countryCode", "country")
    if cc == "countryCode":
        rename["countryCode"] = "country"
    out = df.rename(columns=rename)
    if "company_name" not in out.columns and "title" in out.columns:
        out["company_name"] = out["title"]
    if "email" not in out.columns:
        out["email"] = ""
    return out


def prep(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    work = normalize_columns(df.copy())
    removed_parts: list[pd.DataFrame] = []

    ws_col = "website"
    work = work[work[ws_col].notna() & work[ws_col].astype(str).str.strip().astype(bool)]

    if "totalScore" in work.columns:
        work["totalScore"] = pd.to_numeric(work["totalScore"], errors="coerce")
        work = work[work["totalScore"].fillna(0) >= MIN_SCORE]

    if "reviewsCount" in work.columns:
        work["reviewsCount"] = pd.to_numeric(work["reviewsCount"], errors="coerce")
        work = work[work["reviewsCount"].fillna(0) >= MIN_REVIEWS]

    if "email" in work.columns:
        bad_email = ~work["email"].map(_email_ok)
        removed_parts.append(work.loc[bad_email].copy())
        work = work.loc[~bad_email]

    work["lead_score"] = work.apply(score_row, axis=1)
    work = work.sort_values(by="lead_score", ascending=False)

    dedup_col = "placeId" if "placeId" in work.columns else "google_maps_url"
    if dedup_col not in work.columns:
        dedup_col = "company_name"
    dup_mask = work.duplicated(subset=[dedup_col], keep="first")
    removed_parts.append(work.loc[dup_mask].copy())
    work = work.loc[~dup_mask]

    removed = pd.concat(removed_parts, ignore_index=True) if removed_parts else pd.DataFrame()
    return work, removed


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("input_csv", type=Path)
    ap.add_argument("-o", "--output", type=Path, required=True)
    ap.add_argument("--removed-out", type=Path, default=None)
    ap.add_argument("--sep", default=",", help="Separador CSV de entrada")
    args = ap.parse_args()

    if not args.input_csv.is_file():
        print(f"No existe {args.input_csv}", file=sys.stderr)
        return 1

    df = pd.read_csv(args.input_csv, sep=args.sep, low_memory=False)
    clean, removed = prep(df)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    clean.to_csv(args.output, index=False)
    print(f"Prep: {len(df)} -> {len(clean)} filas -> {args.output}")
    if args.removed_out:
        removed.to_csv(args.removed_out, index=False)
        print(f"Removed: {len(removed)} -> {args.removed_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
