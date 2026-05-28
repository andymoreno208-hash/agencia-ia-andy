from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import pandas as pd
import requests


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "CHARLES_PERSONAL_NAME_STRICT_2.2_two_names_zip_excel.csv"
OUT = ROOT / "CHARLES_PERSONAL_NAME_STRICT_2.3_two_names_zip_filled_osm.csv"
CACHE_PATH = ROOT / "tmp" / "nominatim_zip_cache.json"


ZIP_RE = re.compile(r"\b(\d{5})(?:-\d{4})?\b")


def extract_zip(text: str) -> str:
    m = ZIP_RE.search(text or "")
    return m.group(1) if m else ""


def s(x) -> str:
    if x is None:
        return ""
    if pd.isna(x):
        return ""
    v = str(x).strip()
    return "" if v.lower() in ("nan", "none", "nat") else v


def load_cache() -> Dict[str, str]:
    if not CACHE_PATH.exists():
        return {}
    try:
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_cache(cache: Dict[str, str]) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(cache, indent=2, sort_keys=True), encoding="utf-8")


def query_zip_nominatim(q: str, session: requests.Session) -> Tuple[str, Optional[Dict[str, Any]]]:
    """
    Returns (zip, raw_address_dict)
    """
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": q,
        "format": "jsonv2",
        "addressdetails": 1,
        "limit": 1,
    }
    # Nominatim requires a valid User-Agent identifying your app/email.
    headers = {
        "User-Agent": "VanguardScale-LeadOps/1.0 (contact: andy@local)",
        "Accept-Language": "en",
    }
    r = session.get(url, params=params, headers=headers, timeout=30)
    r.raise_for_status()
    data = r.json()
    if not data:
        return "", None
    addr = data[0].get("address") or {}
    postcode = s(addr.get("postcode", ""))
    return extract_zip(postcode), addr


def main() -> None:
    if not SRC.exists():
        raise SystemExit(f"Missing input: {SRC}")

    df = pd.read_csv(SRC, sep=";", dtype=str, keep_default_na=False, encoding="utf-8-sig")
    for c in df.columns:
        df[c] = df[c].map(s)

    cache = load_cache()
    session = requests.Session()

    filled = 0
    attempted = 0
    skipped_has_zip = 0
    failed = 0

    for i in df.index:
        cur_zip = s(df.at[i, "Zip"])
        if cur_zip.strip():
            skipped_has_zip += 1
            continue

        address = s(df.at[i, "Address"])
        city = s(df.at[i, "City"])
        state = s(df.at[i, "State"])
        if not address or not city or not state:
            continue

        query = f"{address}, {city}, {state}, USA"
        key = query.lower()
        if key in cache:
            z = cache[key]
            if z:
                df.at[i, "Zip"] = z
                filled += 1
            continue

        attempted += 1
        if attempted == 1 or attempted % 10 == 0:
            print(f"progress attempted={attempted} filled_new={filled} failed={failed}")
        try:
            z, _addr = query_zip_nominatim(query, session=session)
        except Exception:
            z = ""

        cache[key] = z
        if z:
            df.at[i, "Zip"] = z
            filled += 1
        else:
            failed += 1

        # Rate-limit: be nice to Nominatim (1 request/sec-ish)
        time.sleep(1.1)
        if attempted % 10 == 0:
            save_cache(cache)

    save_cache(cache)

    # Keep Excel-friendly output
    df.to_csv(OUT, index=False, sep=";", encoding="utf-8-sig")

    print("rows", len(df))
    print("already_had_zip", skipped_has_zip)
    print("attempted", attempted)
    print("filled_new", filled)
    print("failed", failed)
    print("out", OUT)


if __name__ == "__main__":
    main()

