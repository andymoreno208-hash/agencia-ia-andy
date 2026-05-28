#!/usr/bin/env bash
# Enriquece las 60 filas crudas Dallas (email + branch count). Ejecutar en Mac.
set -euo pipefail
cd "$(dirname "$0")/.."

RAW="campaign_outputs/charles_dallas_pilot_raw.csv"
PREP="campaign_outputs/charles_dallas_pilot_60_prep.csv"
OUT="campaign_outputs/charles_dallas_pilot_60_enriched.csv"
TOP="campaign_outputs/charles_pilot_20_dallas_enriched.csv"
LOG="campaign_outputs/charles_enrich_60_log.csv"

echo "== 1/2 Prep 60 filas (formato Charles) =="
python3 scripts/charles_pilot_from_apify_maps.py "$RAW" \
  -o "$PREP" \
  --all-rows

echo "== 2/2 Enrich (dominios únicos, resume OK) =="
# Sin cloudscraper + timeout más alto: corporates suelen colgar con cloudscraper a 75s.
python3 scripts/charles_enrich_pilot.py "$PREP" \
  -o "$OUT" \
  --top-out "$TOP" \
  --top-limit 20 \
  --log-out "$LOG" \
  --resume \
  --no-cloudscraper \
  --delay 0.6 \
  --domain-timeout 150 \
  --max-pages 10

echo "Listo: $OUT"
echo "Top 20 (prioriza email, si no hay suficientes rellena por branch): $TOP"

# Si casi no hay emails, reintentar solo crawl (conserva branch del log):
# python3 scripts/charles_enrich_pilot.py "$PREP" -o "$OUT" --top-out "$TOP" \\
#   --log-out "$LOG" --resume --emails-only --skip-branches \\
#   --no-cloudscraper --domain-timeout 150 --delay 0.6
