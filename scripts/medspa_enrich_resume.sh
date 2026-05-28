#!/usr/bin/env bash
# MedSpa Plano: reanuda desde log. PYTHONUNBUFFERED = ves cada línea al instante.
set -euo pipefail
cd "$(dirname "$0")/.."

export PYTHONUNBUFFERED=1

LOG="campaign_outputs/medspa_us_run1_enrich_log.csv"
echo "=== MedSpa enrich (resume) ==="
echo "Log: $LOG ($(wc -l < "$LOG" 2>/dev/null || echo 0) líneas, incl. header)"
python3 -c "
from pathlib import Path
import sys
sys.path.insert(0, 'scripts')
from enrich_emails_free import load_resume_log
n = len(load_resume_log(Path('$LOG'))[0])
print(f'Dominios ya hechos en log: {n} (el siguiente debería ser {n+1}/154)')
"

caffeinate -i python3 scripts/enrich_emails_free.py \
  campaign_outputs/medspa_us_run1_prep.csv \
  -o campaign_outputs/medspa_us_run1_instantly.csv \
  --enriched-out campaign_outputs/medspa_us_run1_enriched.csv \
  --log-out "$LOG" \
  --resume \
  --no-cloudscraper \
  --sep ',' \
  --delay 0.3 \
  --max-pages 4 \
  --timeout 8 \
  --domain-timeout 40

python3 scripts/export_medspa_instantly_tiers.py campaign_outputs/medspa_us_run1_instantly.csv

echo ""
echo "Listo. Sube: campaign_outputs/medspa_us_run1_instantly_tier_a.csv"
