#!/usr/bin/env python3
import sys
from urllib.parse import urlparse

import pandas as pd

from enrich_decision_makers import norm_url, is_blocked_host


SHEET = "Sheet1"


def main() -> int:
    if len(sys.argv) < 3:
        print("Usage: generate_blocked_queue.py INPUT_XLSX OUTPUT_XLSX", file=sys.stderr)
        return 2

    in_path = sys.argv[1]
    out_path = sys.argv[2]

    df = pd.read_excel(in_path, sheet_name=SHEET)

    for col in ["Decision Maker Name", "Title", "Email", "Website"]:
        if col not in df.columns:
            df[col] = pd.NA

    def website_host(u: str) -> str:
        try:
            return urlparse(u).netloc
        except Exception:
            return ""

    website_norm = df["Website"].apply(norm_url)
    blocked_mask = website_norm.apply(lambda u: bool(u) and is_blocked_host(u))
    missing_email_mask = df["Email"].isna() | (df["Email"].astype(str).str.strip() == "")

    queue = df.loc[blocked_mask & missing_email_mask].copy()
    queue.insert(0, "Blocked Reason", "Cloudflare/anti-bot (manual needed)")
    queue["Website"] = website_norm.loc[queue.index]
    queue.insert(1, "Website Host", queue["Website"].apply(lambda u: website_host(u or "")))

    # Keep just high-signal columns for manual completion
    cols = [
        "Blocked Reason",
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
        queue.to_excel(w, index=False, sheet_name="blocked_queue")

    print(f"Wrote blocked queue: {out_path} (rows: {len(queue)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

