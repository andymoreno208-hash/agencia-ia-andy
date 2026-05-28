from __future__ import annotations

import re
from pathlib import Path
from typing import Optional, Tuple

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

CHARLES_LAST = Path("/Users/andymoreno/Downloads/CHARLES_PERSONAL_NAME_STRICT (1).csv")
GOOGLE_PLACES = [
    Path("/Users/andymoreno/Downloads/dataset_crawler-google-places_2026-04-28_22-01-06-819.csv"),
    Path("/Users/andymoreno/Downloads/dataset_crawler-google-places_2026-04-30_17-24-31-400.csv"),
    Path("/Users/andymoreno/Downloads/dataset_crawler-google-places_2026-04-30_17-36-13-194.csv"),
    Path("/Users/andymoreno/Downloads/dataset_crawler-google-places_2026-04-30_17-48-23-452.csv"),
]

OUT = ROOT / "CHARLES_PERSONAL_NAME_STRICT_2.0.csv"


BAD_EMAIL_PREFIX = re.compile(
    r"^(info|admin|admissions?|office|contact|hello|support|service|enroll(ment)?|registrar)@",
    re.I,
)
BAD_TITLE_PHRASES = re.compile(
    r"\b(call\s+for\s+a\s+tour|talk\s+with\s+our\s+director|working\s+collaboratively|contact\s+details|hours|schedule\s+a\s+tour)\b",
    re.I,
)
EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I)
PHONE_RE = re.compile(r"(\+?1[\s\-\.]?)?\(?\d{3}\)?[\s\-\.]?\d{3}[\s\-\.]?\d{4}")

BAD_NAME_PAT = re.compile(
    r"\b(administration|admin|admissions?|office|staff|directory|faculty|contact|hours|advisor|teacher|directors?)\b",
    re.I,
)

FREE_EMAIL_DOMAINS = {
    "gmail.com",
    "google.com",
    "yahoo.com",
    "outlook.com",
    "hotmail.com",
    "aol.com",
    "icloud.com",
    "me.com",
    "verizon.net",
    "comcast.net",
}


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
    u = u.split("/")[0]
    u = u.split("?")[0]
    u = u.split("#")[0]
    u = u.strip().strip(".")
    if u.startswith("www."):
        u = u[4:]
    return u


def domain_from_email(email: str) -> str:
    e = s(email).strip().lower()
    if "@" not in e:
        return ""
    dom = e.split("@", 1)[1].strip()
    dom = dom.strip(">)].,;\"'")
    if dom.startswith("www."):
        dom = dom[4:]
    return dom


def is_generic_email(email: str) -> bool:
    e = s(email).strip().lower()
    if not e or "@" not in e:
        return True
    if BAD_EMAIL_PREFIX.match(e):
        return True
    return False


def looks_like_person_name(name: str) -> bool:
    n = norm_space(name)
    if not n:
        return False
    if len(n) > 60:
        return False
    if any(ch.isdigit() for ch in n):
        return False
    # Reject obvious scrape artifacts / roles
    if BAD_TITLE_PHRASES.search(n):
        return False
    if BAD_NAME_PAT.search(n):
        return False
    if EMAIL_RE.search(n):
        return False
    if PHONE_RE.search(n):
        return False
    if "," in n:
        # often "Last, First" or scraped lists; keep it strict
        return False
    parts = [p for p in re.split(r"\s+", n) if p]
    # Allow prefixes like Dr.
    if parts and parts[0].lower().rstrip(".") in ("dr", "mr", "mrs", "ms", "rev"):
        parts = parts[1:]
    if len(parts) < 2:
        return False
    if len(parts) > 5:
        return False
    if any(len(p) > 20 for p in parts):
        return False
    return True


def clean_title(title: str) -> str:
    t = norm_space(title)
    if not t:
        return ""
    # Remove emails/phones that got embedded
    t = EMAIL_RE.sub("", t).strip()
    t = PHONE_RE.sub("", t).strip()
    t = re.sub(r"\s+", " ", t).strip(" -–—|,;")
    return t


def title_is_valid(title: str) -> bool:
    t = clean_title(title)
    if not t:
        return False
    if len(t) > 80:
        return False
    if BAD_TITLE_PHRASES.search(t):
        return False
    if "..." in t:
        return False
    if "http" in t.lower():
        return False
    if re.search(r"\boffice of the\b", t, re.I):
        return False
    # Titles shouldn't look like sentences
    if t.count(" ") > 10:
        return False
    return True


def normalize_company(c: str) -> str:
    v = norm_space(c).lower()
    v = re.sub(r"[^a-z0-9 ]+", " ", v)
    v = re.sub(r"\s+", " ", v).strip()
    return v


def build_places_index() -> Tuple[pd.DataFrame, pd.DataFrame]:
    dfs = []
    for p in GOOGLE_PLACES:
        df = pd.read_csv(p, dtype=str, keep_default_na=False)
        for c in df.columns:
            df[c] = df[c].map(s)
        dfs.append(df)
    places = pd.concat(dfs, ignore_index=True).drop_duplicates()

    # indexes: by website domain and by normalized title
    places["website_domain"] = places["website"].map(domain_from_url)
    places["title_norm"] = places["title"].map(normalize_company)

    by_domain = (
        places.sort_values(["reviewsCount", "totalScore"], ascending=False, na_position="last")
        .drop_duplicates(subset=["website_domain"])
        .set_index("website_domain")
    )
    by_title = (
        places.sort_values(["reviewsCount", "totalScore"], ascending=False, na_position="last")
        .drop_duplicates(subset=["title_norm"])
        .set_index("title_norm")
    )
    return by_domain, by_title


def enrich_row(row: pd.Series, by_domain: pd.DataFrame, by_title: pd.DataFrame) -> pd.Series:
    website = s(row.get("Website", ""))
    company = s(row.get("Company", ""))
    email = s(row.get("Email", ""))

    dom = domain_from_url(website) or domain_from_email(email)
    place: Optional[pd.Series] = None

    if dom and dom in by_domain.index:
        place = by_domain.loc[dom]
    else:
        tnorm = normalize_company(company)
        if tnorm and tnorm in by_title.index:
            place = by_title.loc[tnorm]

    if place is not None and isinstance(place, pd.Series):
        # Use Places data to standardize company/address/phone/website
        row["Company"] = s(place.get("title", "")) or company
        row["Address"] = s(place.get("street", "")) or s(row.get("Address", ""))
        row["City"] = s(place.get("city", "")) or s(row.get("City", ""))
        row["State"] = s(place.get("state", "")) or s(row.get("State", ""))
        row["Phone"] = s(place.get("phone", "")) or s(row.get("Phone", ""))
        row["Website"] = s(place.get("website", "")) or website
    return row


def main() -> None:
    df = pd.read_csv(CHARLES_LAST, dtype=str, keep_default_na=False)
    for c in df.columns:
        df[c] = df[c].map(s)

    # Basic normalization
    df["Name"] = df["Name"].map(norm_space)
    df["Title"] = df["Title"].map(norm_space)
    df["Email"] = df["Email"].map(lambda x: s(x).strip())
    df["Company"] = df["Company"].map(norm_space)
    df["Phone"] = df["Phone"].map(norm_space)
    df["Address"] = df["Address"].map(norm_space)
    df["City"] = df["City"].map(norm_space)
    df["State"] = df["State"].map(norm_space)
    df["County"] = df["County"].map(norm_space)
    df["Website"] = df["Website"].map(norm_space)

    # Strict filters (fixing the issues Charles highlighted)
    df["Title_clean"] = df["Title"].map(clean_title)
    mask = pd.Series(True, index=df.index)
    mask &= df["Name"].map(looks_like_person_name)
    def email_ok(e: str) -> bool:
        e = s(e).strip().lower()
        if is_generic_email(e):
            return False
        if not EMAIL_RE.fullmatch(e.strip()):
            return False
        dom = domain_from_email(e)
        if dom in FREE_EMAIL_DOMAINS:
            return False
        return True

    mask &= df["Email"].map(email_ok)
    mask &= df["Title_clean"].map(title_is_valid)
    # Keep required location info
    for col in ["Company", "City", "State", "County"]:
        mask &= df[col].astype(str).str.strip().ne("")

    clean = df.loc[mask].copy()
    clean["Title"] = clean["Title_clean"]
    clean.drop(columns=["Title_clean"], inplace=True)

    # Enrich company/address/phone/website from Places when possible
    by_domain, by_title = build_places_index()
    clean = clean.apply(lambda r: enrich_row(r, by_domain, by_title), axis=1)

    # Final column order
    out_cols = ["Name", "Title", "Email", "Company", "Phone", "Address", "City", "State", "County", "Website"]
    clean = clean[out_cols].copy()

    clean.to_csv(OUT, index=False)

    print("source_rows", len(df))
    print("kept_rows", len(clean))
    print("dropped_rows", len(df) - len(clean))
    print("out", OUT)


if __name__ == "__main__":
    main()

