from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass

from openai import AsyncOpenAI

from .async_crawl import EmailHit
from .config import RadarConfig

SYSTEM_PROMPT = """Eres un extractor B2B. Dado un fragmento de texto web que contiene un email,
devuelve SOLO JSON válido con las claves exactas:
{"nombre_detectado": "...", "cargo": "..."}
Reglas:
- nombre_detectado: nombre completo de persona si existe; si no hay persona, cadena vacía.
- cargo: título/rol profesional en inglés o español; si no hay, cadena vacía.
- No inventes datos que no estén en el texto.
- Sin markdown ni explicación."""


@dataclass
class EnrichedLead:
    email: str
    nombre_detectado: str
    cargo: str
    source_url: str
    website: str
    row: dict


async def _extract_one(
    client: AsyncOpenAI,
    hit: EmailHit,
    cfg: RadarConfig,
) -> EnrichedLead:
    user = (
        f"Email: {hit.email}\n\n"
        f"Fragmento:\n{hit.context[:1200]}"
    )
    last_err: Exception | None = None
    for attempt in range(cfg.llm_max_retries):
        try:
            resp = await client.chat.completions.create(
                model=cfg.openai_model,
                temperature=0,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user},
                ],
            )
            raw = resp.choices[0].message.content or "{}"
            data = json.loads(raw)
            nombre = str(data.get("nombre_detectado") or "").strip()
            cargo = str(data.get("cargo") or "").strip()
            return EnrichedLead(
                email=hit.email,
                nombre_detectado=nombre,
                cargo=cargo,
                source_url=hit.source_url,
                website=hit.website,
                row=hit.row,
            )
        except (json.JSONDecodeError, KeyError, TypeError, Exception) as e:
            last_err = e
            await asyncio.sleep(1.5 * (attempt + 1))
    print(f"[llm] fallo {hit.email}: {last_err}")
    return EnrichedLead(
        email=hit.email,
        nombre_detectado="",
        cargo="",
        source_url=hit.source_url,
        website=hit.website,
        row=hit.row,
    )


async def enrich_hits_with_llm(hits: list[EmailHit], cfg: RadarConfig) -> list[EnrichedLead]:
    if not cfg.openai_api_key:
        print("[llm] OPENAI_API_KEY ausente — nombres/cargos vacíos")
        return [
            EnrichedLead(
                email=h.email,
                nombre_detectado="",
                cargo="",
                source_url=h.source_url,
                website=h.website,
                row=h.row,
            )
            for h in hits
        ]

    client = AsyncOpenAI(api_key=cfg.openai_api_key)
    sem = asyncio.Semaphore(cfg.llm_concurrency)

    async def guarded(h: EmailHit) -> EnrichedLead:
        async with sem:
            return await _extract_one(client, h, cfg)

    out = await asyncio.gather(*[guarded(h) for h in hits])
    print(f"[llm] enriquecidos {len(out)} leads")
    return list(out)
