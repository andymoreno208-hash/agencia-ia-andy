#!/usr/bin/env python3
"""
Separa leads MedSpa para Instantly por riesgo de rebote.

Tier A (send_first): email en dominio del website, no blocklist, MX ok.
Tier B (send_second): info/contact/hello en dominio del website, MX ok.
Do not send: dominio raro, mismatch, blocklist, sin MX.

Uso:
  python3 scripts/export_medspa_instantly_tiers.py \\
    campaign_outputs/medspa_us_run1_instantly.csv
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd

try:
    import dns.resolver

    HAS_DNS = True
except ImportError:
    HAS_DNS = False

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prep_medspa_us_run1 import BLOCKLIST_DOMAIN_SUBSTR, _email_ok  # noqa: E402

SAFE_ROLE_LOCALS = frozenset({"info", "contact", "hello", "office", "appointments", "booking"})
BAD_WEBSITE_HOST = (
    "linktr.ee",
    "instagram.com",
    "facebook.com",
    "vagaro.com",
    "yelp.com",
    "tiktok.com",
)


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


def domains_align(email: str, website: str) -> bool:
    ed = email_domain(email)
    wd = website_domain(website)
    if not ed or not wd:
        return False
    return ed == wd or ed.endswith("." + wd) or wd.endswith("." + ed)


def mx_ok(domain: str, cache: dict[str, bool]) -> bool:
    if domain in cache:
        return cache[domain]
    if not HAS_DNS:
        cache[domain] = True
        return True
    try:
        dns.resolver.resolve(domain, "MX")
        cache[domain] = True
    except Exception:
        try:
            dns.resolver.resolve(domain, "A")
            cache[domain] = True
        except Exception:
            cache[domain] = False
    return cache[domain]


def bounce_reason(row: pd.Series) -> str | None:
    email = str(row.get("email", "") or "").strip().lower()
    if not email or "@" not in email:
        return "no_email"
    if not _email_ok(email):
        return "blocklist_or_invalid"
    web = str(row.get("website", "") or "")
    host = website_domain(web)
    if not host:
        return "no_website"
    if any(b in host for b in BAD_WEBSITE_HOST):
        return "bad_website_host"
    if any(b in email for b in BLOCKLIST_DOMAIN_SUBSTR):
        return "blocklist_domain"
    if not domains_align(email, web):
        return "domain_mismatch"
    local = email.split("@", 1)[0]
    if re.search(r"\.(png|jpg|jpeg|gif|svg|ico)$", local, re.I):
        return "asset_filename"
    return None


def tier_label(row: pd.Series) -> str:
    email = str(row["email"]).lower()
    local = email.split("@", 1)[0]
    if local in SAFE_ROLE_LOCALS:
        return "B_safe_role"
    if local in {"admin", "support", "sales", "reception", "frontdesk"}:
        return "B_risky_role"
    return "A_personal_or_named"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("input_csv", type=Path)
    ap.add_argument(
        "--out-dir",
        type=Path,
        default=Path("campaign_outputs"),
    )
    ap.add_argument("--prefix", default="medspa_us_run1")
    args = ap.parse_args()

    if not args.input_csv.is_file():
        print(f"No existe {args.input_csv}", file=sys.stderr)
        print("Corre antes: python3 scripts/enrich_emails_free.py campaign_outputs/medspa_us_run1_prep.csv ...", file=sys.stderr)
        return 1

    df = pd.read_csv(args.input_csv)
    if "email" not in df.columns:
        print("CSV sin columna email", file=sys.stderr)
        return 1

    df = df.copy()
    df["email"] = df["email"].astype(str).str.strip().str.lower()
    df = df[df["email"].str.contains("@", na=False)]

    mx_cache: dict[str, bool] = {}
    reasons = []
    tiers = []
    mx_flags = []
    for _, row in df.iterrows():
        r = bounce_reason(row)
        reasons.append(r or "")
        if r:
            tiers.append("reject")
            mx_flags.append(False)
        else:
            dom = email_domain(row["email"])
            ok = mx_ok(dom, mx_cache)
            mx_flags.append(ok)
            if not ok:
                reasons.append("no_mx")
                tiers.append("reject")
            else:
                tiers.append(tier_label(row))

    df["bounce_risk"] = reasons
    df["send_tier"] = tiers
    df["mx_ok"] = mx_flags

    reject = df[df["send_tier"] == "reject"].copy()
    tier_a = df[df["send_tier"] == "A_personal_or_named"].copy()
    tier_b = df[df["send_tier"].isin({"B_safe_role", "B_risky_role"})].copy()
    send_first = tier_a.sort_values(by="lead_score", ascending=False, na_position="last")
    send_second = tier_b[tier_b["send_tier"] == "B_safe_role"].sort_values(
        by="lead_score", ascending=False, na_position="last"
    )

    out_cols = [
        "email",
        "company",
        "website",
        "phone",
        "city",
        "state",
        "country",
        "google_maps_url",
        "lead_score",
        "email_source",
        "send_tier",
        "mx_ok",
    ]
    out_cols = [c for c in out_cols if c in df.columns]

    p = args.prefix
    d = args.out_dir
    d.mkdir(parents=True, exist_ok=True)

    def write(name: str, frame: pd.DataFrame) -> None:
        path = d / f"{p}_{name}.csv"
        frame[out_cols].to_csv(path, index=False)
        print(f"  {len(frame):4d} -> {path}")

    print("Export Instantly (anti-rebote):")
    write("instantly_tier_a", send_first)
    write("instantly_tier_b", send_second)
    write("instantly_send_all", pd.concat([send_first, send_second], ignore_index=True))
    write("do_not_send", reject)

    print(
        f"\nSube a Instantly primero: {d}/{p}_instantly_tier_a.csv\n"
        f"Luego (si necesitas volumen): {d}/{p}_instantly_tier_b.csv\n"
        f"Ramp: 20-30/día. Pausa si rebote >2%."
    )
    if not HAS_DNS:
        print("AVISO: pip install dnspython para filtrar dominios sin MX.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
