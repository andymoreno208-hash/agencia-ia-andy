from __future__ import annotations

import re
from pathlib import Path
from typing import List, Optional

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "CHARLES_PERSONAL_NAME_STRICT.csv"
OUT = ROOT / "CHARLES_PERSONAL_NAME_STRICT_2.0_keep79.csv"

# "Previous docs" (Google Places) don't have emails/names/titles,
# but they can help standardize business address/phone/website if needed.
PLACES_FILES = [
    Path("/Users/andymoreno/Downloads/dataset_crawler-google-places_2026-04-28_22-01-06-819.csv"),
    Path("/Users/andymoreno/Downloads/dataset_crawler-google-places_2026-04-30_17-24-31-400.csv"),
    Path("/Users/andymoreno/Downloads/dataset_crawler-google-places_2026-04-30_17-36-13-194.csv"),
    Path("/Users/andymoreno/Downloads/dataset_crawler-google-places_2026-04-30_17-48-23-452.csv"),
]


EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I)
PHONE_RE = re.compile(r"(\+?1[\s\-\.]?)?\(?\d{3}\)?[\s\-\.]?\d{3}[\s\-\.]?\d{4}")
TITLE_PICK_RE = re.compile(
    r"\b(assistant principal|vice principal|principal|head of school|cfo|chief financial officer|finance director|director of finance|business manager|office manager|administrator|director|partner|owner|controller|operations director|practice manager|manager|registrar)\b",
    re.I,
)


def s(x) -> str:
    if x is None:
        return ""
    if pd.isna(x):
        return ""
    v = str(x).strip()
    return "" if v.lower() in ("nan", "none", "nat") else v


def norm_space(v: str) -> str:
    return re.sub(r"\s+", " ", s(v)).strip()


def domain_from_url(url: str) -> str:
    u = s(url).strip().lower()
    if not u:
        return ""
    u = re.sub(r"^https?://", "", u)
    u = u.split("/")[0].split("?")[0].split("#")[0]
    u = u.strip().strip(".")
    if u.startswith("www."):
        u = u[4:]
    return u


def normalize_company(c: str) -> str:
    v = norm_space(c).lower()
    v = re.sub(r"[^a-z0-9 ]+", " ", v)
    v = re.sub(r"\s+", " ", v).strip()
    return v


def extract_emails(text: str) -> List[str]:
    return [m.group(0).strip() for m in EMAIL_RE.finditer(text or "")]


def extract_phone(text: str) -> Optional[str]:
    m = PHONE_RE.search(text or "")
    return m.group(0).strip() if m else None


def is_row_bad(name: str, title: str, email: str) -> bool:
    blob = " ".join([name, title, email]).lower()
    # Only touch rows with clear cross-column artifacts
    if "..." in blob:
        return True
    if "http" in blob:
        return True
    if EMAIL_RE.search(name) or EMAIL_RE.search(title):
        return True
    if PHONE_RE.search(name) or PHONE_RE.search(title):
        return True
    # long sentence-ish title
    if len(title.strip()) > 80:
        return True
    # classic phrase artifacts Charles pointed out
    if any(
        k in blob
        for k in [
            "call for a tour",
            "talk with our director",
            "working collaboratively",
            "contact details",
            "schedule a tour",
            "email hours phone",
            "filter by a to z",
            "office of the chief",
        ]
    ):
        return True
    return False


def cleanup_text_keep_meaning(text: str) -> str:
    t = norm_space(text)
    if not t:
        return ""
    t = EMAIL_RE.sub("", t)
    t = PHONE_RE.sub("", t)
    t = re.sub(r"\s+", " ", t).strip(" -–—|,;")
    return t


def pick_title_fallback(text: str) -> Optional[str]:
    """
    If title is a scraped sentence, try to reduce it to a plausible role keyword.
    We prefer specific multi-word titles first (regex order matters).
    """
    t = norm_space(text).lower()
    if not t:
        return None
    m = TITLE_PICK_RE.search(t)
    if not m:
        return None
    picked = m.group(1).strip()
    # Normalize common variants
    norm = {
        "chief financial officer": "Chief Financial Officer",
        "cfo": "CFO",
        "assistant principal": "Assistant Principal",
        "vice principal": "Vice Principal",
        "principal": "Principal",
        "head of school": "Head of School",
        "director of finance": "Director of Finance",
        "finance director": "Finance Director",
        "business manager": "Business Manager",
        "office manager": "Office Manager",
        "practice manager": "Practice Manager",
        "operations director": "Operations Director",
        "administrator": "Administrator",
        "director": "Director",
        "controller": "Controller",
        "partner": "Partner",
        "owner": "Owner",
        "registrar": "Registrar",
        "manager": "Manager",
    }
    return norm.get(picked.lower(), picked.title())


def build_places_index() -> tuple[pd.DataFrame, pd.DataFrame]:
    dfs = []
    for p in PLACES_FILES:
        df = pd.read_csv(p, dtype=str, keep_default_na=False)
        for c in df.columns:
            df[c] = df[c].map(s)
        dfs.append(df)
    places = pd.concat(dfs, ignore_index=True).drop_duplicates()
    places["website_domain"] = places["website"].map(domain_from_url)
    places["title_norm"] = places["title"].map(normalize_company)

    by_domain = places.drop_duplicates(subset=["website_domain"]).set_index("website_domain")
    by_title = places.drop_duplicates(subset=["title_norm"]).set_index("title_norm")
    return by_domain, by_title


def enrich_business_fields(row: pd.Series, by_domain: pd.DataFrame, by_title: pd.DataFrame) -> pd.Series:
    # Only fill blanks; do not override non-blank good data
    website = s(row.get("Website", ""))
    company = s(row.get("Company", ""))

    place = None
    dom = domain_from_url(website)
    if dom and dom in by_domain.index:
        place = by_domain.loc[dom]
    else:
        tnorm = normalize_company(company)
        if tnorm and tnorm in by_title.index:
            place = by_title.loc[tnorm]

    if place is None or not isinstance(place, pd.Series):
        return row

    def fill(col: str, src_col: str) -> None:
        if norm_space(row.get(col, "")) == "":
            row[col] = s(place.get(src_col, ""))

    fill("Company", "title")
    fill("Address", "street")
    fill("City", "city")
    fill("State", "state")
    fill("Phone", "phone")
    fill("Website", "website")
    return row


def main() -> None:
    df = pd.read_csv(SRC, dtype=str, keep_default_na=False)
    for c in df.columns:
        df[c] = df[c].map(s)

    by_domain, by_title = build_places_index()

    fixed_count = 0
    enriched_count = 0

    for i in df.index:
        name = norm_space(df.at[i, "Name"])
        title = norm_space(df.at[i, "Title"])
        email = norm_space(df.at[i, "Email"])

        # Enrich business fields only if blank (safe)
        before = (df.at[i, "Company"], df.at[i, "Address"], df.at[i, "Phone"], df.at[i, "Website"])
        row = enrich_business_fields(df.loc[i].copy(), by_domain, by_title)
        after = (row.get("Company", ""), row.get("Address", ""), row.get("Phone", ""), row.get("Website", ""))
        if before != after:
            df.loc[i] = row
            enriched_count += 1

        if not is_row_bad(name, title, email):
            continue

        # Fix crossed-column artifacts without dropping the row
        blob = " ".join([name, title, email])
        emails = extract_emails(blob)
        phones = [p for p in [extract_phone(name), extract_phone(title)] if p]

        # If Email column doesn't look like a single email but we can extract one, set it.
        if (not EMAIL_RE.fullmatch(email)) and emails:
            df.at[i, "Email"] = emails[0]

        # Remove embedded emails/phones/sentences from Title/Name
        cleaned_title = cleanup_text_keep_meaning(title)
        df.at[i, "Name"] = cleanup_text_keep_meaning(name)

        # If phone column blank but we extracted one, fill phone
        if norm_space(df.at[i, "Phone"]) == "" and phones:
            df.at[i, "Phone"] = phones[0]

        # Final normalization: trim very long titles (keep some meaning)
        t2 = norm_space(cleaned_title)
        # If still looks like a sentence, downgrade to a plausible role keyword
        if (
            len(t2) > 55
            or any(
                k in t2.lower()
                for k in [
                    "call for a tour",
                    "talk with our director",
                    "working collaboratively",
                    "contact details",
                    "email hours phone",
                    "filter by a to z",
                    "office of the chief",
                    "schedule a tour",
                ]
            )
            or "..." in t2
        ):
            picked = pick_title_fallback(blob)
            df.at[i, "Title"] = picked or "Administrator"
        else:
            # Keep cleaned title; only trim if absurdly long
            if len(t2) > 80:
                t2 = t2[:77].rstrip() + "..."
            df.at[i, "Title"] = t2

        fixed_count += 1

    out_cols = ["Name", "Title", "Email", "Company", "Phone", "Address", "City", "State", "County", "Website"]
    df[out_cols].to_csv(OUT, index=False)

    print("rows_in", len(df))
    print("rows_out", len(df))
    print("fixed_rows", fixed_count)
    print("enriched_rows_blank_filled", enriched_count)
    print("out", OUT)


if __name__ == "__main__":
    main()

