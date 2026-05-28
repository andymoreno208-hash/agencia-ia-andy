from __future__ import annotations

import asyncio
import time
from typing import Any

from .config import RadarConfig


def _sync_run_apify(cfg: RadarConfig) -> list[dict[str, Any]]:
    from apify_client import ApifyClient

    if not cfg.apify_token:
        raise ValueError("APIFY_TOKEN no configurado")
    if not cfg.apify_input:
        raise ValueError("apify_input vacío — pasa --apify-input JSON o dict en código")

    client = ApifyClient(cfg.apify_token)
    actor_id = cfg.apify_actor_id
    print(f"[apify] Lanzando actor {actor_id}…")
    run = client.actor(actor_id).call(run_input=cfg.apify_input)
    run_id = run["id"]
    dataset_id = run["defaultDatasetId"]
    print(f"[apify] Run {run_id} OK — dataset {dataset_id}")

    items: list[dict[str, Any]] = []
    for item in client.dataset(dataset_id).iterate_items():
        items.append(dict(item))
    print(f"[apify] {len(items)} items en memoria")
    return items


async def fetch_apify_dataset(cfg: RadarConfig) -> list[dict[str, Any]]:
    """Dispara actor, espera fin y descarga dataset a memoria (thread pool)."""
    return await asyncio.to_thread(_sync_run_apify, cfg)


def wait_existing_run(cfg: RadarConfig, run_id: str) -> list[dict[str, Any]]:
    """Reanuda un run ya iniciado (síncrono, para --apify-run-id)."""
    from apify_client import ApifyClient

    client = ApifyClient(cfg.apify_token)
    started = time.time()
    while True:
        run = client.run(run_id).get()
        status = run["status"]
        print(f"[apify] run={run_id} status={status} ({int(time.time() - started)}s)")
        if status in ("SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"):
            if status != "SUCCEEDED":
                raise RuntimeError(f"Apify run terminó: {status}")
            dataset_id = run["defaultDatasetId"]
            return [dict(x) for x in client.dataset(dataset_id).iterate_items()]
        if time.time() - started > cfg.apify_max_wait_sec:
            raise TimeoutError(f"Run {run_id} timeout")
        time.sleep(cfg.apify_poll_sec)
