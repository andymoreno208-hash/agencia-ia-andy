#!/usr/bin/env bash
# Diagnóstico rápido de Jarvis en Mac
set -u

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
JARVIS_DIR="${REPO_ROOT}/scripts/jarvis"

echo "==> Jarvis doctor"
echo "Repo: ${REPO_ROOT}"
echo "Sistema: $(uname -s) $(uname -m)"
echo ""

check() {
  local label="$1"
  local path="$2"
  if [[ -e "$path" ]]; then
    echo "OK  ${label}: ${path}"
  else
    echo "FALTA ${label}: ${path}"
  fi
}

check "jarvis_serve.py" "${REPO_ROOT}/scripts/jarvis_serve.py"
check "briefing.sh" "${JARVIS_DIR}/briefing.sh"
check "local-briefing.py" "${JARVIS_DIR}/local-briefing.py"
check "install.sh" "${JARVIS_DIR}/install.sh"
check "comando jarvis" "${HOME}/.local/bin/jarvis"

if command -v jarvis >/dev/null 2>&1; then
  echo "OK  jarvis en PATH: $(command -v jarvis)"
else
  echo "FALTA jarvis en PATH (corre: ./scripts/jarvis/install.sh)"
fi

if [[ "$(uname -s)" == "Darwin" ]]; then
  if command -v say >/dev/null 2>&1; then
    echo "OK  voz macOS (say)"
  else
    echo "FALTA say"
  fi
  if command -v osascript >/dev/null 2>&1; then
    echo "OK  notificaciones (osascript)"
  else
    echo "FALTA osascript"
  fi
else
  echo "AVISO: no estás en macOS; jarvis solo habla en Mac"
fi

echo ""
echo "Prueba:"
echo "  python3 ${REPO_ROOT}/scripts/jarvis_serve.py briefing --text"
