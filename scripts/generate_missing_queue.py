#!/usr/bin/env python3
import sys
from urllib.parse import urlparse

import pandas as pd

from enrich_decision_makers import norm_url, is_blocked_host


SHEET = "Sheet1"


def main() -> int:
    if len(sys.argv) < 3:
        print("Usage: generate_missing_queue.py ENRICHED_XLSX OUTPUT_XLSX", file=sys.stderr)
        return 2

    in_path = sys.argv[1]
    out_path = sys.argv[2]

    df = pd.read_excel(in_path, sheet_name=SHEET)

    for col in ["Decision Maker Name", "Title", "Email", "Website"]:
        if col not in df.columns:
            df[col] = pd.NA

    def host(u: str) -> str:
        try:
            return urlparse(u).netloc
        except Exception:
            return ""

    website_norm = df["Website"].apply(norm_url)
    blocked_mask = website_norm.apply(lambda u: bool(u) and is_blocked_host(u))
    missing_email_mask = df["Email"].isna() | (df["Email"].astype(str).str.strip() == "")

    queue = df.loc[(~blocked_mask) & missing_email_mask].copy()
    queue.insert(0, "Queue Reason", "Not blocked; no decision-maker email found (manual review)")
    queue["Website"] = website_norm.loc[queue.index]
    queue.insert(1, "Website Host", queue["Website"].apply(lambda u: host(u or "")))

    cols = [
        "Queue Reason",
        "Website Host",
        "School Name",
        "Decision Maker Name",
        "Title",
        "Email",
        "Website",
        "Phone",
        "Address",
        "City",
        "State",
    ]
    cols = [c for c in cols if c in queue.columns]
    queue = queue[cols]

    with pd.ExcelWriter(out_path, engine="openpyxl") as w:
        queue.to_excel(w, index=False, sheet_name="missing_queue")

    print(f"Wrote missing queue: {out_path} (rows: {len(queue)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

