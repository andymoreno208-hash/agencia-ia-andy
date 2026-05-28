from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from .async_crawl import normalize_apify_row


def load_csv_rows(path: Path, sep: str = ";") -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return [dict(row) for row in csv.DictReader(f, delimiter=sep)]


def load_json_rows(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return [dict(x) for x in data]
    if isinstance(data, dict) and "items" in data:
        return [dict(x) for x in data["items"]]
    raise ValueError("JSON debe ser lista o {items: [...]}")


def normalize_rows(raw: list[dict[str, Any]], from_apify: bool) -> list[dict[str, Any]]:
    if from_apify:
        return [normalize_apify_row(x) for x in raw]
    return raw


OUT_FIELDS = [
    "email",
    "decision_maker_name",
    "title",
    "company",
    "website",
    "phone",
    "city",
    "state",
    "country",
    "google_maps_url",
    "lead_score",
    "email_source_url",
    "smtp_status",
]


def write_output_csv(path: Path, rows: list[dict[str, str]], smtp_detail: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=OUT_FIELDS, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            r.setdefault("smtp_status", smtp_detail.get(r["email"], "skipped"))
            w.writerow(r)


def leads_to_rows(leads: list[Any], smtp_detail: dict[str, str]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for ld in leads:
        row = ld.row if hasattr(ld, "row") else {}
        out.append(
            {
                "email": ld.email,
                "decision_maker_name": getattr(ld, "nombre_detectado", "") or "",
                "title": getattr(ld, "cargo", "") or "",
                "company": str(row.get("company_name") or ""),
                "website": getattr(ld, "website", "") or str(row.get("website") or ""),
                "phone": str(row.get("phone") or ""),
                "city": str(row.get("city") or ""),
                "state": str(row.get("state") or ""),
                "country": str(row.get("country") or ""),
                "google_maps_url": str(row.get("google_maps_url") or ""),
                "lead_score": str(row.get("lead_score") or ""),
                "email_source_url": getattr(ld, "source_url", "") or "",
                "smtp_status": smtp_detail.get(ld.email, "250 OK"),
            }
        )
    return out
