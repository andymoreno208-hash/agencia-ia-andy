#!/usr/bin/env python3
"""Serve Rex Jarvis dashboard on http://127.0.0.1:8765"""

from __future__ import annotations

import argparse
import http.server
import socket
import subprocess
import sys
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JARVIS = ROOT / "jarvis"
PORT = 8765


def sync_config() -> None:
    sync_script = ROOT / "scripts/jarvis_sync.py"
    subprocess.run([sys.executable, str(sync_script)], check=False)


def jarvis_alive(port: int) -> bool:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=1) as resp:
            return resp.status == 200
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


def pid_on_port(port: int) -> str | None:
    try:
        out = subprocess.check_output(["lsof", "-ti", f":{port}"], text=True).strip()
        return out.splitlines()[0] if out else None
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Rex Jarvis local dashboard")
    parser.add_argument("--no-sync", action="store_true", help="Skip activos.md sync")
    parser.add_argument("--open", action="store_true", help="Open browser")
    parser.add_argument("--stop", action="store_true", help="Kill server on port and exit")
    parser.add_argument("--port", type=int, default=PORT)
    args = parser.parse_args()

    url = f"http://127.0.0.1:{args.port}/"

    if args.stop:
        pid = pid_on_port(args.port)
        if pid:
            subprocess.run(["kill", pid], check=False)
            print(f"Jarvis detenido (PID {pid})")
        else:
            print(f"Nada corriendo en puerto {args.port}")
        return

    if not args.no_sync:
        sync_config()

    if port_in_use(args.port):
        if jarvis_alive(args.port):
            print(f"Jarvis ya corre → {url}")
            if args.open:
                webbrowser.open(url)
            print("Para reiniciar: python3 scripts/jarvis_serve.py --stop")
            return
        pid = pid_on_port(args.port)
        print(f"Puerto {args.port} ocupado por otro proceso (PID {pid}).")
        print(f"  kill {pid}   # o: python3 scripts/jarvis_serve.py --stop")
        sys.exit(1)

    handler = http.server.SimpleHTTPRequestHandler

    class JarvisHandler(handler):
        def __init__(self, *a, **kw):
            super().__init__(*a, directory=str(JARVIS), **kw)

        def log_message(self, fmt, *log_args):
            pass  # silencio en terminal

    server = http.server.ThreadingHTTPServer(("127.0.0.1", args.port), JarvisHandler)
    print(f"Jarvis → {url}")
    print("Fullscreen monitor externo: Ctrl+Cmd+F")
    print("Detener: Ctrl+C  |  python3 scripts/jarvis_serve.py --stop")
    if args.open:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nJarvis off.")
        server.shutdown()


if __name__ == "__main__":
    main()
