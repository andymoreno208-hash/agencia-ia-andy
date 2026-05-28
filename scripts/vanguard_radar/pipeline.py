from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .apify_orchestrator import fetch_apify_dataset, wait_existing_run
from .async_crawl import crawl_all_rows
from .config import RadarConfig
from .io_loaders import (
    leads_to_rows,
    load_csv_rows,
    load_json_rows,
    normalize_rows,
    write_output_csv,
)
from .llm_extract import enrich_hits_with_llm
from .smtp_validate import filter_deliverable


async def run_pipeline(
    cfg: RadarConfig,
    *,
    input_csv: Path | None = None,
    input_json: Path | None = None,
    apify_run_id: str | None = None,
    output_csv: Path,
    csv_sep: str = ";",
) -> dict[str, Any]:
    """
    Orquestación V4:
      1) Apify | CSV | JSON → filas normalizadas
      2) Crawl async (aiohttp)
      3) LLM (gpt-4o-mini)
      4) SMTP RCPT → solo válidos al CSV final
    """
    from_apify = False
    if apify_run_id:
        raw = wait_existing_run(cfg, apify_run_id)
        from_apify = True
    elif cfg.apify_input is not None:
        raw = await fetch_apify_dataset(cfg)
        from_apify = True
    elif input_csv:
        raw = load_csv_rows(input_csv, csv_sep)
    elif input_json:
        raw = load_json_rows(input_json)
    else:
        raise ValueError("Fuente vacía: --apify-input, --input-csv o --input-json")

    rows = normalize_rows(raw, from_apify=from_apify)
    print(f"[pipeline] {len(rows)} filas de entrada")

    hits = await crawl_all_rows(rows, cfg)
    if not hits:
        write_output_csv(output_csv, [], {})
        return {"input_rows": len(rows), "emails_found": 0, "output_rows": 0}

    enriched = await enrich_hits_with_llm(hits, cfg)
    deliverable, smtp_results = await filter_deliverable(enriched, cfg)
    smtp_map = {r.email: r.detail for r in smtp_results}

    out_rows = leads_to_rows(deliverable, smtp_map)
    write_output_csv(output_csv, out_rows, smtp_map)

    stats = {
        "input_rows": len(rows),
        "emails_found": len(hits),
        "after_llm": len(enriched),
        "after_smtp": len(deliverable),
        "output_rows": len(out_rows),
        "output_csv": str(output_csv),
    }
    print(f"[pipeline] listo: {json.dumps(stats)}")
    return stats
