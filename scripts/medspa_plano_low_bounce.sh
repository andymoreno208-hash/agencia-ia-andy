#!/usr/bin/env bash
# Plano MedSpa -> Instantly con mínimos rebotes (email-only).
set -euo pipefail
cd "$(dirname "$0")/.."

SRC="${1:-/Users/andymoreno/Downloads/dataset_crawler-google-places_2026-05-15_15-52-08-578.csv}"
RAW="campaign_outputs/medspa_us_run1_apify.csv"
PREP="campaign_outputs/medspa_us_run1_prep.csv"
INST="campaign_outputs/medspa_us_run1_instantly.csv"
ENR="campaign_outputs/medspa_us_run1_enriched.csv"

cp "$SRC" "$RAW"
echo "== Prep (dedupe, 4★+, reviews 15+, website) =="
python3 scripts/prep_medspa_us_run1.py "$RAW" -o "$PREP" --sep ','

echo "== Enrich emails desde website (Mac, ~10-15 min) =="
python3 scripts/enrich_emails_free.py "$PREP" \
  -o "$INST" \
  --enriched-out "$ENR" \
  --sep ',' \
  --delay 0.6 \
  --max-pages 12 \
  --cloudscraper

echo "== Tiers anti-rebote =="
python3 scripts/export_medspa_instantly_tiers.py "$INST"

echo ""
echo "LISTO. Import en Instantly:"
echo "  1) campaign_outputs/medspa_us_run1_instantly_tier_a.csv  (menos rebotes)"
echo "  2) si falta volumen: medspa_us_run1_instantly_tier_b.csv"
echo "  NO subir: medspa_us_run1_do_not_send.csv"
