from __future__ import annotations

import html as html_lib
import json
import re

from .hygiene import EMAIL_RE, norm_email

MAILTO_RE = re.compile(
    r"mailto:\s*([a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[^\"'\s>]+)",
    re.IGNORECASE,
)
LD_JSON_BLOCK = re.compile(
    r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>',
    re.IGNORECASE | re.DOTALL,
)
JSON_EMAIL_KV = re.compile(
    r'"(?:email|contactEmail|mail|correo|e-mail)"\s*:\s*"([^"]+)"',
    re.IGNORECASE,
)


def strip_tags(html: str) -> str:
    html = re.sub(r"(?is)<script[^>]*>.*?</script>", " ", html)
    html = re.sub(r"(?is)<style[^>]*>.*?</style>", " ", html)
    html = re.sub(r"(?is)<[^>]+>", " ", html)
    return html_lib.unescape(html)


def _walk_json_for_email(obj: object, found: set[str]) -> None:
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k.lower() in ("email", "e-mail") and isinstance(v, str):
                ne = norm_email(v)
                if ne:
                    found.add(ne)
            else:
                _walk_json_for_email(v, found)
    elif isinstance(obj, list):
        for it in obj:
            _walk_json_for_email(it, found)


def extract_ld_json_emails(html: str) -> set[str]:
    found: set[str] = set()
    for m in LD_JSON_BLOCK.finditer(html):
        blob = m.group(1).strip()
        if not blob:
            continue
        candidates = [blob]
        if blob.count("{") > 1:
            candidates.extend(part.strip() for part in re.split(r"\}\s*\{", blob) if part.strip())
        for piece in candidates:
            piece = piece.strip()
            if not piece.startswith(("{", "[")):
                continue
            try:
                data = json.loads(piece)
            except json.JSONDecodeError:
                continue
            _walk_json_for_email(data, found)
    return found


def extract_emails_with_context(html: str, window: int = 200) -> list[tuple[str, str]]:
    """Devuelve (email_normalizado, contexto_plano) por cada match en texto visible."""
    plain = strip_tags(html)
    hits: list[tuple[str, str]] = []
    seen: set[str] = set()

    for m in MAILTO_RE.finditer(html):
        ne = norm_email(m.group(1))
        if ne and ne not in seen:
            seen.add(ne)
            hits.append((ne, plain[:window] if plain else ne))

    for ne in extract_ld_json_emails(html):
        if ne not in seen:
            seen.add(ne)
            hits.append((ne, plain[:window] if plain else ne))

    for m in JSON_EMAIL_KV.finditer(html):
        ne = norm_email(m.group(1))
        if ne and ne not in seen:
            seen.add(ne)
            hits.append((ne, plain[:window] if plain else ne))

    for m in EMAIL_RE.finditer(plain):
        ne = norm_email(m.group(0))
        if not ne or ne in seen:
            continue
        seen.add(ne)
        start = max(0, m.start() - window)
        end = min(len(plain), m.end() + window)
        hits.append((ne, plain[start:end]))

    return hits
