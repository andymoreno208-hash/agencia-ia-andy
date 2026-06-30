#!/usr/bin/env python3
"""Jarvis en Mac: briefing por voz + servidor local para push de n8n."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
JARVIS_DIR = ROOT / "jarvis"
LOCAL_BRIEFING = JARVIS_DIR / "local-briefing.py"
BRIEFING_SH = JARVIS_DIR / "briefing.sh"

HOST = os.environ.get("JARVIS_LISTENER_HOST", "127.0.0.1")
PORT = int(os.environ.get("JARVIS_LISTENER_PORT", "8765"))
VOICE = os.environ.get("JARVIS_VOICE", "Monica")
LOG_FILE = Path(os.environ.get("JARVIS_LOG", Path.home() / ".jarvis" / "briefing.log"))


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


def load_local_briefing() -> dict[str, str]:
    spec = importlib.util.spec_from_file_location("local_briefing", LOCAL_BRIEFING)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"No encuentro {LOCAL_BRIEFING}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.build_briefing()


def run_briefing_shell(mode: str) -> int:
    if not BRIEFING_SH.is_file():
        raise FileNotFoundError(f"No encuentro {BRIEFING_SH}")
    result = subprocess.run([str(BRIEFING_SH), mode], check=False)
    return result.returncode


def deliver_briefing(*, text_only: bool = False, speak_aloud: bool = True) -> dict[str, str]:
    require_mac()
    payload = load_local_briefing()
    title = payload.get("title", "Briefing Jarvis")
    text = str(payload.get("text", "")).strip()
    if not text:
        raise RuntimeError("Briefing vacío")

    log(f"Briefing generado ({len(text)} chars)")
    if text_only:
        print(f"{title}\n\n{text}")
        return payload

    notify(title, "Briefing listo. Jarvis está hablando.")
    if speak_aloud:
        speak(text)
    return payload


class JarvisHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        if self.path not in ("/briefing", "/health"):
            self.send_error(404, "Not found")
            return

        if self.path == "/health":
            self._json_response({"ok": True})
            return

        payload = deliver_briefing(text_only=True, speak_aloud=False)
        self._json_response(payload)

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
            payload = load_local_briefing()
            text = str(payload.get("text", "")).strip()
            title = str(payload.get("title", "Briefing Jarvis"))

        if not text:
            self.send_error(400, "Missing text")
            return

        log(f"POST /briefing ({len(text)} chars)")
        notify(title, "Jarvis tiene tu briefing.")
        speak(text)
        self._json_response({"ok": True, "title": title})

    def _json_response(self, payload: dict) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        log(format % args)


def serve() -> int:
    require_mac()
    server = ThreadingHTTPServer((HOST, PORT), JarvisHandler)
    log(f"Escuchando en http://{HOST}:{PORT}")
    print(f"Jarvis escuchando en http://{HOST}:{PORT}/briefing")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log("Detenido")
        return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Jarvis — briefing y servidor en Mac")
    sub = parser.add_subparsers(dest="command")

    briefing = sub.add_parser("briefing", help="Genera y habla el briefing")
    briefing.add_argument("--text", action="store_true", help="Solo imprimir texto")
    briefing.add_argument("--notify", action="store_true", help="Solo notificación")

    sub.add_parser("serve", help="Servidor local para push de n8n")
    sub.add_parser("install", help="Instala launchd y comando jarvis")

    args = parser.parse_args(argv)
    command = args.command or "briefing"

    if command == "install":
        install_sh = JARVIS_DIR / "install.sh"
        if not install_sh.is_file():
            raise SystemExit(f"No encuentro {install_sh}. Haz git pull origin main")
        return subprocess.call([str(install_sh)])

    if command == "serve":
        return serve()

    if command == "briefing":
        if args.text:
            deliver_briefing(text_only=True, speak_aloud=False)
            return 0
        if args.notify:
            payload = deliver_briefing(text_only=True, speak_aloud=False)
            notify(payload["title"], payload["text"][:220])
            return 0
        deliver_briefing()
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
