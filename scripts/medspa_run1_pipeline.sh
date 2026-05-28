#!/usr/bin/env bash
# Pipeline Run 1 MedSpa US: Apify -> prep -> enrich -> Tier A Instantly
set -euo pipefail
cd "$(dirname "$0")/.."

APIFY_RAW="campaign_outputs/medspa_us_run1_apify.csv"
PREP="campaign_outputs/medspa_us_run1_prep.csv"
ENRICHED="campaign_outputs/medspa_us_run1_enriched.csv"
INSTANTLY="campaign_outputs/medspa_us_run1_instantly.csv"
TIER_A="campaign_outputs/medspa_us_run1_instantly_tier_a.csv"

if [[ -z "${APIFY_TOKEN:-}" ]]; then
  echo "APIFY_TOKEN no definido. Exporta el token o coloca el CSV en ${APIFY_RAW} manualmente."
  exit 1
fi

echo "== 1/4 Apify Run 1 =="
python3 scripts/run_apify_medspa_run1.py -o "$APIFY_RAW"

echo "== 2/4 Prep (dedupe + filtros) =="
python3 scripts/prep_medspa_us_run1.py "$APIFY_RAW" -o "$PREP" \
  --removed-out campaign_outputs/medspa_us_run1_removed.csv

echo "== 3/4 Enrich emails (Mac / WiFi) =="
python3 scripts/enrich_emails_free.py "$PREP" \
  -o "$INSTANTLY" \
  --enriched-out "$ENRICHED" \
  --sep ','

echo "== 4/4 Tier A Instantly =="
python3 scripts/filter_instantly_tier_a.py "$INSTANTLY" -o "$TIER_A"

echo ""
echo "Listo. Sube a Instantly: $TIER_A"
echo "Ramp sugerido: 20-30 emails/día por dominio de envío."
