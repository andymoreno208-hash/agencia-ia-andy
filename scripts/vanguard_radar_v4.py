#!/usr/bin/env python3
"""
Vanguard Radar V4 — Apify → crawl async → LLM → SMTP RCPT → CSV

Instalar:
  pip install aiohttp aiosmtplib apify-client openai dnspython

Variables de entorno:
  APIFY_TOKEN   — obligatorio si usas --apify-input
  OPENAI_API_KEY — obligatorio para extracción semántica (sin key: nombres vacíos)

Ejemplos:
  # Solo CSV local (sin Apify)
  python scripts/vanguard_radar_v4.py \\
    --input-csv campaign_outputs/dataset_places_ec_prep.csv \\
    -o campaign_outputs/radar_v4_out.csv --sep ';' --skip-smtp

  # Apify end-to-end
  export APIFY_TOKEN=...
  export OPENAI_API_KEY=...
  python scripts/vanguard_radar_v4.py \\
    --apify-actor nwua9Gu5YrADL7ZDj \\
    --apify-input campaign_outputs/apify_medspa_us_run1_input.json \\
    -o campaign_outputs/radar_v4_medspa.csv \\
    --http-concurrency 80
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

# Permite ejecutar desde raíz del repo
_REPO = Path(__file__).resolve().parent
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from vanguard_radar.config import RadarConfig
from vanguard_radar.pipeline import run_pipeline


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Vanguard Radar V4")
    src = ap.add_mutually_exclusive_group()
    src.add_argument("--input-csv", type=Path, help="CSV prep (website, company_name, …)")
    src.add_argument("--input-json", type=Path, help="JSON lista de leads")
    ap.add_argument(
        "--apify-input",
        type=Path,
        help="JSON input del Actor Apify (dispara run automático)",
    )
    ap.add_argument("--apify-run-id", help="Reanudar run existente y solo procesar dataset")
    ap.add_argument(
        "--apify-actor",
        default="YOUR_ACTOR_ID_HERE",
        help="ID del Actor Apify (placeholder por defecto)",
    )
    ap.add_argument("-o", "--output", type=Path, required=True)
    ap.add_argument("--sep", default=";", help="Separador CSV entrada")
    ap.add_argument("--http-concurrency", type=int, default=50)
    ap.add_argument("--llm-concurrency", type=int, default=20)
    ap.add_argument("--smtp-concurrency", type=int, default=15)
    ap.add_argument("--max-paths", type=int, default=6)
    ap.add_argument("--include-social", action="store_true")
    ap.add_argument(
        "--skip-smtp",
        action="store_true",
        help="No validar SMTP (puerto 25 suele estar bloqueado en ISP)",
    )
    return ap.parse_args()


def build_config(args: argparse.Namespace) -> RadarConfig:
    cfg = RadarConfig(
        apify_actor_id=args.apify_actor,
        http_concurrency=args.http_concurrency,
        llm_concurrency=args.llm_concurrency,
        smtp_concurrency=args.smtp_concurrency,
        max_contact_paths=args.max_paths,
        include_social=args.include_social,
        skip_smtp=args.skip_smtp,
    )
    if args.apify_input:
        if not args.apify_input.is_file():
            raise FileNotFoundError(args.apify_input)
        cfg.apify_input = json.loads(args.apify_input.read_text(encoding="utf-8"))
    return cfg


async def async_main() -> int:
    args = parse_args()
    cfg = build_config(args)

    if args.apify_input or args.apify_run_id:
        if not cfg.apify_token:
            print("Error: exporta APIFY_TOKEN", file=sys.stderr)
            return 1

    try:
        await run_pipeline(
            cfg,
            input_csv=args.input_csv,
            input_json=args.input_json,
            apify_run_id=args.apify_run_id,
            output_csv=args.output,
            csv_sep=args.sep,
        )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    return 0


def main() -> int:
    return asyncio.run(async_main())


if __name__ == "__main__":
    raise SystemExit(main())
