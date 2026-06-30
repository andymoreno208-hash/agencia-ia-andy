#!/usr/bin/env bash
# Instala Jarvis briefing en Mac (launchd + atajo de teclado opcional)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
JARVIS_HOME="${HOME}/.jarvis"
LAUNCH_AGENTS="${HOME}/Library/LaunchAgents"
ENV_FILE="${JARVIS_HOME}/briefing.env"
ENV_EXAMPLE="${SCRIPT_DIR}/briefing.env.example"

echo "==> Jarvis Mac Briefing — instalación"
mkdir -p "$JARVIS_HOME" "$LAUNCH_AGENTS"
chmod +x "${SCRIPT_DIR}/briefing.sh" "${SCRIPT_DIR}/listener.py" "${SCRIPT_DIR}/local-briefing.py" "${SCRIPT_DIR}/jarvis"

if [[ ! -f "$ENV_FILE" ]]; then
  cp "$ENV_EXAMPLE" "$ENV_FILE"
  echo "Creado $ENV_FILE (opcional)."
fi

BIN_DIR="${HOME}/.local/bin"
mkdir -p "$BIN_DIR"
ln -sf "${SCRIPT_DIR}/jarvis" "${BIN_DIR}/jarvis"
echo "Comando global: ${BIN_DIR}/jarvis (asegúrate de que ~/.local/bin esté en tu PATH)"

install_plist() {
  local template="$1"
  local target_name="$2"
  local target="${LAUNCH_AGENTS}/${target_name}"
  sed \
    -e "s|__JARVIS_SCRIPT_DIR__|${SCRIPT_DIR}|g" \
    -e "s|__JARVIS_HOME__|${HOME}|g" \
    "${SCRIPT_DIR}/${template}" >"$target"
  echo "Instalado $target"
}

install_plist "com.vanguard.jarvis.briefing.plist" "com.vanguard.jarvis.briefing.plist"
install_plist "com.vanguard.jarvis.listener.plist" "com.vanguard.jarvis.listener.plist"

launchctl bootout "gui/$(id -u)/com.vanguard.jarvis.briefing" 2>/dev/null || true
launchctl bootout "gui/$(id -u)/com.vanguard.jarvis.listener" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "${LAUNCH_AGENTS}/com.vanguard.jarvis.listener.plist"
launchctl bootstrap "gui/$(id -u)" "${LAUNCH_AGENTS}/com.vanguard.jarvis.briefing.plist"

echo ""
echo "Listo. Prueba ahora:"
echo "  jarvis"
echo "  # o: ${SCRIPT_DIR}/briefing.sh"
echo ""
echo "Atajo recomendado (Atajos de macOS):"
echo "  Acción: Ejecutar script de shell → ${SCRIPT_DIR}/briefing.sh"
echo "  Nombre: Jarvis Briefing"
echo "  Atajo: ⌃⌥⌘B"
echo ""
echo "En n8n importa n8n-jarvis-briefing-mac.json y configura credenciales."
