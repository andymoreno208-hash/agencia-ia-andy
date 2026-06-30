#!/usr/bin/env python3
"""Servidor local en Mac para recibir push del cron de n8n y hablar el briefing."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HOST = os.environ.get("JARVIS_LISTENER_HOST", "127.0.0.1")
PORT = int(os.environ.get("JARVIS_LISTENER_PORT", "8765"))
VOICE = os.environ.get("JARVIS_VOICE", "Monica")
LOG_FILE = Path(os.environ.get("JARVIS_LOG", Path.home() / ".jarvis" / "briefing.log"))


def log(message: str) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as handle:
        handle.write(f"[listener] {message}\n")


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


class BriefingHandler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/briefing":
            self.send_error(404, "Not found")
            return

        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)

        try:
            payload = json.loads(body.decode("utf-8"))
            text = str(payload.get("text", "")).strip()
            title = str(payload.get("title", "Briefing Jarvis"))
        except json.JSONDecodeError:
            self.send_error(400, "Invalid JSON")
            return

        if not text:
            self.send_error(400, "Missing text")
            return

        log(f"Push recibido ({len(text)} chars)")
        notify(title, "Jarvis tiene tu briefing matutino.")
        speak(text)

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"ok": True}).encode("utf-8"))

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        log(format % args)


def main() -> int:
    server = ThreadingHTTPServer((HOST, PORT), BriefingHandler)
    log(f"Escuchando en http://{HOST}:{PORT}/briefing")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log("Detenido")
        return 0


if __name__ == "__main__":
    sys.exit(main())
