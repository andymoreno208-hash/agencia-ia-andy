#!/usr/bin/env python3
"""Jarvis en Mac: servidor local + briefing por voz."""

from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import webbrowser
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
JARVIS_DIR = ROOT / "jarvis"
PID_FILE = Path.home() / ".jarvis" / "serve.pid"
LOG_FILE = Path.home() / ".jarvis" / "briefing.log"

HOST = os.environ.get("JARVIS_LISTENER_HOST", "127.0.0.1")
DEFAULT_PORT = int(os.environ.get("JARVIS_LISTENER_PORT", "8765"))
VOICE = os.environ.get("JARVIS_VOICE", "Monica")
TZ = ZoneInfo(os.environ.get("JARVIS_TZ", "America/Guayaquil"))
OWNER = os.environ.get("JARVIS_OWNER", "Andy")


def require_mac() -> None:
    if sys.platform != "darwin":
        raise SystemExit("Jarvis solo funciona en macOS.")


def log(message: str) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as handle:
        handle.write(f"[jarvis_serve] {message}\n")


def notify(title: str, message: str) -> None:
    safe_title = title.replace('"', '\\"')
    safe_message = message.replace('"', '\\"')[:220]
    subprocess.run(
        [
            "osascript",
            "-e",
            f'display notification "{safe_message}" with title "{safe_title}" sound name "Glass"',
        ],
        check=False,
    )


def speak(text: str) -> None:
    subprocess.run(["say", "-v", VOICE, "-r", "190", text], check=True)


def run_applescript(script: str) -> str:
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


def calendar_events() -> list[str]:
    script = r'''
set startOfDay to current date
set hours of startOfDay to 0
set minutes of startOfDay to 0
set seconds of startOfDay to 0
set endOfDay to startOfDay + (1 * days)
set lines to {}
tell application "Calendar"
  repeat with cal in calendars
    try
      repeat with evt in (every event of cal whose start date ≥ startOfDay and start date < endOfDay)
        set end of lines to ((time string of (start date of evt)) & " — " & (summary of evt))
      end repeat
    end try
  end repeat
end tell
if (count of lines) is 0 then return ""
set AppleScript's text item delimiters to linefeed
return lines as text
'''
    raw = run_applescript(script)
    if not raw:
        return []
    return [line.strip() for line in raw.splitlines() if line.strip()]


def reminders_today() -> list[str]:
    script = r'''
set lines to {}
tell application "Reminders"
  repeat with lst in lists
    repeat with r in (reminders of lst whose completed is false)
      if due date of r is not missing value then
        set d to due date of r
        set todayStart to current date
        set time of todayStart to 0
        set todayEnd to todayStart + (1 * days)
        if d ≥ todayStart and d < todayEnd then
          set end of lines to (name of r as text)
        end if
      end if
    end repeat
  end repeat
end tell
if (count of lines) is 0 then return ""
set AppleScript's text item delimiters to linefeed
return lines as text
'''
    raw = run_applescript(script)
    if not raw:
        return []
    return [line.strip() for line in raw.splitlines() if line.strip()]


def build_briefing(*, sync: bool = True) -> dict[str, str]:
    now = datetime.now(TZ)
    weekdays = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
    months = [
        "enero", "febrero", "marzo", "abril", "mayo", "junio",
        "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
    ]
    fecha = f"{weekdays[now.weekday()]}, {now.day} de {months[now.month - 1]} de {now.year}"

    events = calendar_events() if sync else []
    tasks = reminders_today() if sync else []

    parts = [f"Buenos días, {OWNER}. Hoy es {fecha}.", "", "Agenda de hoy:"]
    if events:
        parts.extend(f"- {event}" for event in events[:8])
    else:
        parts.append("- No tienes eventos en el calendario. Buen día para trabajo profundo.")

    parts.extend(["", "Recordatorios para hoy:"])
    if tasks:
        parts.extend(f"- {task}" for task in tasks[:6])
    else:
        parts.append("- Sin recordatorios pendientes con fecha de hoy.")

    parts.extend(
        [
            "",
            "Prioridades Vanguard Scale:",
            "- Revisar leads nuevos y responder en menos de 3 minutos.",
            "- Avanzar onboarding de clientes activos.",
            "- Una acción de crecimiento: contenido, outreach o mejora del funnel.",
            "",
            "Buen día. Estoy aquí cuando necesites el siguiente briefing.",
        ]
    )

    return {
        "title": "Briefing Jarvis",
        "text": "\n".join(parts),
        "generated_at": now.isoformat(),
        "source": "local" if sync else "local-no-sync",
    }


def deliver_briefing(*, text_only: bool = False, speak_aloud: bool = True, sync: bool = True) -> dict[str, str]:
    require_mac()
    payload = build_briefing(sync=sync)
    title = payload["title"]
    text = payload["text"].strip()
    log(f"Briefing generado ({len(text)} chars, sync={sync})")

    if text_only:
        print(f"{title}\n\n{text}")
        return payload

    notify(title, "Briefing listo. Jarvis está hablando.")
    if speak_aloud:
        speak(text)
    return payload


def stop_server(port: int) -> int:
    stopped = False
    if PID_FILE.exists():
        try:
            pid = int(PID_FILE.read_text().strip())
            os.kill(pid, signal.SIGTERM)
            stopped = True
            log(f"Detenido PID {pid}")
        except (ProcessLookupError, ValueError, PermissionError):
            pass
        PID_FILE.unlink(missing_ok=True)

    result = subprocess.run(["lsof", "-ti", f"tcp:{port}"], capture_output=True, text=True, check=False)
    for pid in result.stdout.split():
        if pid.strip():
            subprocess.run(["kill", pid.strip()], check=False)
            stopped = True

    if stopped:
        print(f"Jarvis detenido (puerto {port}).")
        return 0
    print(f"No había Jarvis corriendo en el puerto {port}.")
    return 0


class JarvisHandler(BaseHTTPRequestHandler):
    server_port: int = DEFAULT_PORT

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            self._json({"ok": True})
            return
        if self.path == "/briefing":
            self._json(deliver_briefing(text_only=True, speak_aloud=False))
            return
        self.send_error(404, "Not found")

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/briefing":
            self.send_error(404, "Not found")
            return

        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)
        if body:
            try:
                payload = json.loads(body.decode("utf-8"))
                text = str(payload.get("text", "")).strip()
                title = str(payload.get("title", "Briefing Jarvis"))
            except json.JSONDecodeError:
                self.send_error(400, "Invalid JSON")
                return
        else:
            payload = build_briefing()
            text = payload["text"]
            title = payload["title"]

        if not text:
            self.send_error(400, "Missing text")
            return

        notify(title, "Jarvis tiene tu briefing.")
        speak(text)
        self._json({"ok": True, "title": title})

    def _json(self, payload: dict) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        log(format % args)


def serve(port: int, *, open_browser: bool = False) -> int:
    require_mac()
    stop_server(port)

    server = ThreadingHTTPServer((HOST, port), JarvisHandler)
    PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    PID_FILE.write_text(str(os.getpid()))
    url = f"http://{HOST}:{port}/briefing"
    log(f"Escuchando en {url}")
    print(f"Jarvis escuchando en {url}")

    if open_browser:
        webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log("Detenido por teclado")
        return 0
    finally:
        PID_FILE.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Jarvis — briefing y servidor en Mac")
    parser.add_argument(
        "command",
        nargs="?",
        choices=("briefing", "serve", "install"),
        help="briefing: hablar ahora | serve: servidor | install: launchd",
    )
    parser.add_argument("--briefing", action="store_true", help="Genera y habla el briefing")
    parser.add_argument("--text", action="store_true", help="Solo imprimir texto del briefing")
    parser.add_argument("--no-sync", action="store_true", help="Briefing sin leer Calendario/Recordatorios")
    parser.add_argument("--open", action="store_true", help="Abrir /briefing en el navegador al iniciar")
    parser.add_argument("--stop", action="store_true", help="Detener servidor Jarvis")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"Puerto (default {DEFAULT_PORT})")

    args = parser.parse_args(argv)
    sync = not args.no_sync

    if args.stop:
        return stop_server(args.port)

    if args.briefing or args.command == "briefing":
        deliver_briefing(text_only=args.text, speak_aloud=not args.text, sync=sync)
        return 0

    if args.command == "install":
        install_sh = JARVIS_DIR / "install.sh"
        if not install_sh.is_file():
            raise SystemExit(
                "No encuentro scripts/jarvis/install.sh.\n"
                "Primero sincroniza el repo:\n"
                "  git fetch origin main && git merge origin/main"
            )
        return subprocess.call([str(install_sh)])

    if args.command == "serve" or args.open:
        return serve(args.port, open_browser=args.open)

    # Compatibilidad: sin argumentos → briefing (lo que pides al decir "jarvis")
    deliver_briefing(sync=sync)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
