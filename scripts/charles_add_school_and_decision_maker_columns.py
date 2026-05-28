from __future__ import annotations

import re
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "CHARLES_PERSONAL_NAME_STRICT_2.0_keep79.csv"
OUT = ROOT / "CHARLES_PERSONAL_NAME_STRICT_2.2_two_names_zip_excel.csv"

PLACES_FILES = [
    Path("/Users/andymoreno/Downloads/dataset_crawler-google-places_2026-04-28_22-01-06-819.csv"),
    Path("/Users/andymoreno/Downloads/dataset_crawler-google-places_2026-04-30_17-24-31-400.csv"),
    Path("/Users/andymoreno/Downloads/dataset_crawler-google-places_2026-04-30_17-36-13-194.csv"),
    Path("/Users/andymoreno/Downloads/dataset_crawler-google-places_2026-04-30_17-48-23-452.csv"),
]


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


ZIP_RE = re.compile(r"\b(\d{5})(?:-\d{4})?\b")


def extract_zip(address: str) -> str:
    m = ZIP_RE.search(address or "")
    return m.group(1) if m else ""


def main() -> None:
    df = pd.read_csv(SRC, dtype=str, keep_default_na=False)
    for c in df.columns:
        df[c] = df[c].map(s)

    by_domain, by_title = build_places_index()

    # Create the two "name" columns explicitly
    df["Decision_Maker_Name"] = df["Name"].map(norm_space)

    def school_name(row: pd.Series) -> str:
        company = norm_space(row.get("Company", ""))
        website = norm_space(row.get("Website", ""))
        dom = domain_from_url(website)
        if dom and dom in by_domain.index:
            return norm_space(by_domain.loc[dom].get("title", "")) or company
        tnorm = normalize_company(company)
        if tnorm and tnorm in by_title.index:
            return norm_space(by_title.loc[tnorm].get("title", "")) or company
        return company

    df["School_Name"] = df.apply(school_name, axis=1)
    df["Zip"] = df["Address"].map(extract_zip)

    out_cols = [
        "School_Name",
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
    ]
    # Excel (ES locale) often expects ';' instead of ','.
    # Also write UTF-8 BOM so Excel opens it cleanly.
    df[out_cols].to_csv(OUT, index=False, sep=";", encoding="utf-8-sig")
    print("rows", len(df))
    print("out", OUT)


if __name__ == "__main__":
    main()

