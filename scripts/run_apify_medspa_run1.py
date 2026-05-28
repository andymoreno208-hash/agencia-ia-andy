#!/usr/bin/env python3
"""
Lanza Google Maps Scraper (Compass) Run 1 y descarga CSV a campaign_outputs/.

Requiere: APIFY_TOKEN en el entorno.

Uso:
  python3 scripts/run_apify_medspa_run1.py
  python3 scripts/run_apify_medspa_run1.py --input campaign_outputs/apify_medspa_us_run1_input.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ACTOR_ID = "nwua9Gu5YrADL7ZDj"
DEFAULT_INPUT = Path("campaign_outputs/apify_medspa_us_run1_input.json")
DEFAULT_OUT = Path("campaign_outputs/medspa_us_run1_apify.csv")
POLL_SEC = 15
MAX_WAIT_SEC = 3600


def api(method: str, path: str, token: str, body: dict | None = None) -> dict:
    url = f"https://api.apify.com/v2{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode())


def run_actor(token: str, actor_input: dict) -> str:
    res = api("POST", f"/acts/{ACTOR_ID}/runs", token, {"input": actor_input})
    run_id = res["data"]["id"]
    print(f"Run iniciado: {run_id}")
    print(f"  https://console.apify.com/actors/{ACTOR_ID}/runs/{run_id}")
    return run_id


def wait_run(token: str, run_id: str) -> dict:
    started = time.time()
    while True:
        res = api("GET", f"/actor-runs/{run_id}", token)
        data = res["data"]
        status = data["status"]
        print(f"  status={status} ({int(time.time() - started)}s)")
        if status in ("SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"):
            return data
        if time.time() - started > MAX_WAIT_SEC:
            raise TimeoutError(f"Run {run_id} no terminó en {MAX_WAIT_SEC}s")
        time.sleep(POLL_SEC)


def download_dataset_csv(token: str, dataset_id: str, out_path: Path) -> None:
    url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?format=csv&clean=true"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=300) as resp:
        raw = resp.read()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(raw)
    print(f"CSV guardado: {out_path} ({len(raw)} bytes)")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    ap.add_argument("-o", "--output", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--run-id", default=None, help="Reanudar: solo descargar dataset de un run existente")
    args = ap.parse_args()

    token = os.environ.get("APIFY_TOKEN", "").strip()
    if not token:
        print("Error: exporta APIFY_TOKEN", file=sys.stderr)
        return 1

    try:
        if args.run_id:
            data = wait_run(token, args.run_id)
            if data["status"] != "SUCCEEDED":
                print(f"Run terminó con {data['status']}", file=sys.stderr)
                return 1
            dataset_id = data["defaultDatasetId"]
        else:
            if not args.input.is_file():
                print(f"No existe {args.input}", file=sys.stderr)
                return 1
            actor_input = json.loads(args.input.read_text(encoding="utf-8"))
            run_id = run_actor(token, actor_input)
            data = wait_run(token, run_id)
            if data["status"] != "SUCCEEDED":
                print(f"Run terminó con {data['status']}", file=sys.stderr)
                return 1
            dataset_id = data["defaultDatasetId"]

        download_dataset_csv(token, dataset_id, args.output)
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        print(f"HTTP {e.code}: {body}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
