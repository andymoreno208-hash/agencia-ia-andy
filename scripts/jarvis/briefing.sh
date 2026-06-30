#!/usr/bin/env bash
# Jarvis — briefing matutino en Mac (voz + notificación)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${JARVIS_ENV_FILE:-$HOME/.jarvis/briefing.env}"

if [[ -f "$ENV_FILE" ]]; then
  # shellcheck disable=SC1090
  source "$ENV_FILE"
fi

: "${N8N_BRIEFING_WEBHOOK_URL:?Configura N8N_BRIEFING_WEBHOOK_URL en $ENV_FILE}"
VOICE="${JARVIS_VOICE:-Monica}"
CACHE_DIR="${JARVIS_CACHE_DIR:-$HOME/.jarvis/cache}"
CACHE_FILE="$CACHE_DIR/last-briefing.json"
LOG_FILE="${JARVIS_LOG:-$HOME/.jarvis/briefing.log}"

mkdir -p "$CACHE_DIR" "$(dirname "$LOG_FILE")"

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >>"$LOG_FILE"
}

notify() {
  local title="$1"
  local message="$2"
  osascript -e "display notification \"${message//\"/\\\"}\" with title \"${title//\"/\\\"}\" sound name \"Glass\""
}

speak() {
  local text="$1"
  say -v "$VOICE" -r 190 "$text"
}

fetch_briefing() {
  local response
  response="$(curl -fsSL \
    -H "User-Agent: JarvisMac/1.0" \
    -H "Accept: application/json" \
    --max-time 120 \
    "$N8N_BRIEFING_WEBHOOK_URL")"
  echo "$response" >"$CACHE_FILE"
  echo "$response"
}

extract_field() {
  local json="$1"
  local field="$2"
  echo "$json" | python3 -c '
import json, sys
field = sys.argv[1]
data = json.load(sys.stdin)
value = data.get(field, "")
if not isinstance(value, str):
    value = str(value)
print(value.strip())
' "$field"
}

main() {
  local mode="${1:-speak}"
  local json title text

  log "Iniciando briefing (modo: $mode)"
  notify "Jarvis" "Preparando tu briefing..."

  if ! json="$(fetch_briefing)"; then
    log "Error al obtener briefing desde n8n"
    notify "Jarvis" "No pude conectar con n8n. Revisa la URL del webhook."
    exit 1
  fi

  title="$(extract_field "$json" "title")"
  text="$(extract_field "$json" "text")"

  if [[ -z "$text" ]]; then
    log "Respuesta vacía: $json"
    notify "Jarvis" "El briefing llegó vacío. Revisa el workflow en n8n."
    exit 1
  fi

  log "Briefing recibido (${#text} caracteres)"

  case "$mode" in
    text)
      printf '%s\n\n%s\n' "$title" "$text"
      ;;
    notify)
      notify "${title:-Briefing Jarvis}" "${text:0:220}"
      ;;
    speak|*)
      notify "${title:-Briefing Jarvis}" "Briefing listo. Jarvis está hablando."
      speak "$text"
      ;;
  esac

  log "Briefing completado"
}

main "$@"
