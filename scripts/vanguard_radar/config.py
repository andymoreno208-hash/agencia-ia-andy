from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class RadarConfig:
    """Configuración del pipeline (env + CLI)."""

    # Apify
    apify_token: str = field(default_factory=lambda: os.environ.get("APIFY_TOKEN", "").strip())
    apify_actor_id: str = "YOUR_ACTOR_ID_HERE"  # p. ej. nwua9Gu5YrADL7ZDj (Google Maps)
    apify_input: dict | None = None
    apify_poll_sec: float = 15.0
    apify_max_wait_sec: float = 3600.0

    # HTTP crawl
    http_concurrency: int = 50
    http_timeout: float = 22.0
    max_contact_paths: int = 6
    include_social: bool = False

    # OpenAI
    openai_api_key: str = field(default_factory=lambda: os.environ.get("OPENAI_API_KEY", "").strip())
    openai_model: str = "gpt-4o-mini"
    llm_concurrency: int = 20
    llm_max_retries: int = 3

    # SMTP
    smtp_concurrency: int = 15
    smtp_timeout: float = 12.0
    smtp_helo: str = "vanguard-radar.local"
    smtp_mail_from: str = "verify@vanguard-radar.local"
    skip_smtp: bool = False

    user_agent: str = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    )
