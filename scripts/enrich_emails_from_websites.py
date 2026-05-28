#!/usr/bin/env python3
"""
enrich_emails_from_websites.py — V4 (Vanguard Radar)

Async crawl con aiohttp + verificación real de correos (MX + SMTP RCPT) + decode de
Cloudflare email obfuscation + descubrimiento por sitemap.xml + trust score por
fila. Mantiene la entrada/salida CSV del script anterior y agrega columnas
nuevas para diligencia y entrega buyer-facing.

Highlights:
- aiohttp + asyncio.Semaphore(N) — escanea cientos de sitios en paralelo.
- Timeout corto (default 8s) + backoff exponencial en 429/503 — no se cuelga
  en sitios muertos; pasa al siguiente sin trabar el batch.
- Cloudflare email-protection decode (data-cfemail) — recupera correos que el
  script anterior dejaba escapar.
- DNS MX + SMTP RCPT real-time (`aiosmtplib`) — vende "live mailbox check"
  honesto, con disclaimers (catch-all / port 25 / timeout) por fila.
- Sitemap.xml priorizando URLs con `contact|team|about|kontakt|impressum|...`.
- Detector de bot-block (Cloudflare challenge, captcha) → marca dominio para
  fallback con Apify / proxy si se justifica.
- Trust score por email (0–100): combina fuente + MX + SMTP status + catch-all
  + heurística genérica vs decisor.
- --resume: salta dominios ya escritos en el output (atómico, append).
- JSONL log opcional por corrida (auditoría / debug / dispute-proof).
- LLM extraction opcional (gpt-4o-mini) en el chunk con email para sacar
  nombre + cargo cuando regex no alcanza — feature-flag `--use-llm`.

Buyer disclaimer obligatorio (jamás prometer "0% bounce"): catch-all + port 25
bloqueado + grey listing se reportan por fila en `smtp_status` y `is_catchall`.

Uso típico:
  pip install -r scripts/requirements-vanguard-radar.txt

  python scripts/enrich_emails_from_websites.py \
    campaign_outputs/dataset_places_ec_prep.csv \
    -o campaign_outputs/instantly_from_ec_prep.csv \
    --sep ';' --concurrency 20 --timeout 8 \
    --use-sitemap --check-smtp --resume --jsonl-log

Para entornos locales donde el ISP bloquea el puerto 25 (común en residencial):
  ...  --check-smtp --skip-smtp-probe

  → ejecuta MX-check pero **no** intenta RCPT; deja smtp_status="port25_skipped".
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import html as html_lib
import json
import os
import re
import socket
import ssl
import sys
import time
import urllib.parse
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    import aiohttp
except ImportError as e:
    print(
        "ERROR: aiohttp no instalado. Ejecuta:\n"
        "  pip install -r scripts/requirements-vanguard-radar.txt",
        file=sys.stderr,
    )
    raise

try:
    import aiosmtplib
    HAS_AIOSMTP = True
except ImportError:
    HAS_AIOSMTP = False

try:
    import dns.resolver
    HAS_DNS = True
except ImportError:
    HAS_DNS = False

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

try:
    import cloudscraper
    HAS_CLOUDSCRAPER = True
except ImportError:
    HAS_CLOUDSCRAPER = False


# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

CONTACT_PATHS = (
    "",
    "/contact",
    "/contact/",
    "/contacto",
    "/contacto/",
    "/contacts",
    "/es/contacto",
    "/en/contact",
    "/paginas/contactanos",
    "/contactanos",
    "/about",
    "/about/",
    "/about-us",
    "/nosotros",
    "/equipo",
    "/team",
    "/team/",
    "/our-team",
    "/kontakt",
    "/contato",
    "/contattaci",
    "/nous-contacter",
    "/contactez-nous",
    "/imprint",
    "/impressum",
    "/legal-notice",
    "/aviso-legal",
)

SITEMAP_PATHS = ("/sitemap.xml", "/sitemap_index.xml")

PRIORITY_TOKENS = (
    "contact",
    "team",
    "about",
    "equipo",
    "nosotros",
    "impressum",
    "kontakt",
    "contato",
    "contattaci",
    "nous-contacter",
    "staff",
    "leadership",
    "people",
)

EMAIL_RE = re.compile(
    r"[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@"
    r"[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?"
    r"(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)+",
    re.IGNORECASE,
)

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

CF_EMAIL_RE = re.compile(r'data-cfemail="([0-9a-fA-F]+)"')

OBFUSC_RE = re.compile(
    r"([a-zA-Z0-9._%+-]+)\s*(?:\[at\]|\(at\)|\s+at\s+|&#64;|&#x40;)\s*"
    r"([a-zA-Z0-9.-]+)\s*(?:\[dot\]|\(dot\)|\s+dot\s+|&#46;|\.)\s*([a-zA-Z]{2,10})",
    re.IGNORECASE,
)

JSON_ESCAPE_PREFIX_RE = re.compile(r'^u00[0-9a-f]{2}', re.IGNORECASE)

BOT_BLOCK_PATTERNS = (
    re.compile(r"just a moment", re.IGNORECASE),
    re.compile(r"cf-chl-bypass", re.IGNORECASE),
    re.compile(r"<title>\s*(?:captcha|attention required|access denied)", re.IGNORECASE),
    re.compile(r"checking your browser", re.IGNORECASE),
    re.compile(r"cloudflare ray id", re.IGNORECASE),
)

SKIP_HOST_SUBSTRINGS = (
    "instagram.com",
    "facebook.com",
    "fb.com",
    "tiktok.com",
    "twitter.com",
    "x.com",
    "linkedin.com",
    "youtube.com",
    "youtu.be",
    "wa.me",
    "maps.google",
    "google.com/maps",
    "goo.gl",
    "g.co",
)

GENERIC_LOCAL = frozenset(
    {
        "noreply",
        "no-reply",
        "donotreply",
        "do-not-reply",
        "mailer-daemon",
        "postmaster",
        "webmaster",
        "hostmaster",
        "abuse",
        "privacy",
        "legal",
        "newsletter",
        "news",
        "bounce",
        "mail",
        "spam-trap",
        "spamtrap",
        "spam-trap-no-reply",
        "honeypot",
    }
)

# emails que no son "decisor" pero sí válidos — penalizan confidence pero se conservan
GENERIC_BUT_USEFUL = frozenset(
    {
        "info",
        "contact",
        "hello",
        "ventas",
        "admin",
        "support",
        "sales",
        "ola",
        "hola",
        "office",
        "team",
    }
)

PLACEHOLDER_DOMAINS = frozenset(
    {
        "example.com",
        "example.org",
        "example.net",
        "example.invalid",
        "test.com",
        "test.invalid",
        "domain.com",
        "yourdomain.com",
        "your-domain.com",
        "youremail.com",
        "yourname.com",
        "email.com",
        "mail.com",
        "localhost",
        "sentry.io",
        "wixpress.com",
        "wix.com",
        "jsdelivr.net",
        "unpkg.com",
        "parastorage.com",
        "cloudflare.com",
        "googleapis.com",
        "gstatic.com",
        "cloudfront.net",
        "jquery.com",
        "bootstrap.com",
        "fontawesome.com",
        "fonts.googleapis.com",
    }
)

PLACEHOLDER_DOMAIN_SUBSTRINGS = (
    "jsdelivr",
    "unpkg",
    "parastorage",
    "cdn.",
    "/cdn/",
    "/npm/",
    "/dist/",
    "googleapis",
    "gstatic",
    "cloudfront",
)

INVALID_TLDS = frozenset(
    {
        "invalid",
        "test",
        "localhost",
        "local",
        "example",
        "js",
        "css",
        "json",
        "min",
        "map",
        "html",
        "htm",
        "xml",
        "txt",
        "pdf",
        "png",
        "jpg",
        "jpeg",
        "gif",
        "webp",
        "svg",
        "ico",
        "woff",
        "woff2",
        "ttf",
        "eot",
        "otf",
        "mp4",
        "mp3",
        "zip",
        "rar",
    }
)

SOURCE_BASE_SCORE = {
    "mailto": 40,
    "cf_decode": 35,
    "ld_json": 30,
    "json_kv": 25,
    "csv_original": 25,
    "csv_row": 20,
    "llm_extracted": 22,
    "plain_text": 15,
    "html_raw": 10,
}

LLM_EXTRACT_PROMPT = (
    "Extract the person's full name and job title associated with the given email "
    "from this short HTML/text snippet. Reply STRICTLY as compact JSON with keys "
    '"name" and "title". If unknown, set value to empty string. No prose, no '
    "backticks."
)


# ---------------------------------------------------------------------------
# Helpers de normalización (compatibles con script anterior)
# ---------------------------------------------------------------------------

def _norm_email(raw: str) -> Optional[str]:
    if not raw:
        return None
    e = raw.strip().strip('"').strip("'").rstrip(".,);")
    if "@" not in e:
        return None
    el = e.lower()

    if el.startswith(("http:", "https:", "//", "/", "www.", "ftp:")):
        return None
    if any(ch in el for ch in (" ", "\t", "\n", "\\", "?", "#", "<", ">", "[", "]", "{", "}", "|", "^", "`")):
        return None
    if "/" in el:
        return None

    if el.count("@") != 1:
        return None

    if el.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico",
                    ".js", ".css", ".json", ".min", ".map", ".woff", ".woff2",
                    ".ttf", ".eot", ".otf", ".html", ".htm", ".xml")):
        return None

    if re.match(r"^[a-z0-9._-]+@[123]x\.", el):
        return None

    if not EMAIL_RE.fullmatch(el):
        return None

    local, _, domain = el.partition("@")

    if not local or not domain:
        return None
    if len(local) > 64 or len(el) > 254:
        return None
    if ".." in el:
        return None

    if any(s in domain for s in PLACEHOLDER_DOMAIN_SUBSTRINGS):
        return None
    if domain in PLACEHOLDER_DOMAINS or any(domain.endswith("." + p) for p in PLACEHOLDER_DOMAINS):
        return None

    parts = domain.split(".")
    if len(parts) < 2:
        return None
    tld = parts[-1]
    if not tld or len(tld) < 2:
        return None
    if any(ch.isdigit() for ch in tld):
        return None
    if tld in INVALID_TLDS:
        return None
    if not tld.isalpha():
        return None

    sld = parts[-2] if len(parts) >= 2 else ""
    if not sld or len(sld) < 1:
        return None
    if sld.isdigit():
        return None

    for p in parts[:-1]:
        if p and p.replace("-", "").isdigit() and len(p) >= 2:
            return None

    if local in GENERIC_LOCAL:
        return None
    return el


def should_skip_url(url: str, include_social: bool) -> bool:
    if not url or not url.startswith(("http://", "https://")):
        return True
    low = url.lower()
    if include_social:
        return False
    return any(s in low for s in SKIP_HOST_SUBSTRINGS)


def canonicalize_website(raw: str) -> Optional[str]:
    s = (raw or "").strip().strip('"')
    if not s:
        return None
    if s.startswith("//"):
        s = "https:" + s
    if not s.startswith("http"):
        s = "https://" + s
    parts = urllib.parse.urlsplit(s)
    if not parts.netloc:
        return None
    return urllib.parse.urlunsplit(
        (parts.scheme or "https", parts.netloc, parts.path or "/", parts.query, "")
    )


def join_url(base: str, path: str) -> str:
    if not path:
        return base
    return urllib.parse.urljoin(base.rstrip("/") + "/", path.lstrip("/"))


def url_variants(url: str) -> list[str]:
    """Misma ruta/query; prueba https/http y host con/sin www."""
    p = urllib.parse.urlsplit(url)
    scheme, netloc, path, query, fragment = p
    hosts: list[str] = [netloc]
    if netloc.startswith("www."):
        bare = netloc[4:]
        if bare and bare not in hosts:
            hosts.append(bare)
    else:
        w = "www." + netloc
        if w not in hosts:
            hosts.append(w)
    out: list[str] = []
    seen: set[str] = set()
    for h in hosts:
        for sch in ("https", "http"):
            u = urllib.parse.urlunsplit((sch, h, path or "/", query, fragment))
            if u not in seen:
                seen.add(u)
                out.append(u)
    return out


def strip_tags(html: str) -> str:
    html = re.sub(r"(?is)<script[^>]*>.*?</script>", " ", html)
    html = re.sub(r"(?is)<style[^>]*>.*?</style>", " ", html)
    html = re.sub(r"(?is)<[^>]+>", " ", html)
    return html_lib.unescape(html)


# ---------------------------------------------------------------------------
# Cloudflare email obfuscation decode
# ---------------------------------------------------------------------------

def decode_cf_email(hex_str: str) -> Optional[str]:
    """Decode Cloudflare's data-cfemail XOR obfuscation."""
    try:
        data = bytes.fromhex(hex_str)
        if len(data) < 2:
            return None
        key = data[0]
        return "".join(chr(b ^ key) for b in data[1:])
    except (ValueError, IndexError):
        return None


def extract_cf_emails(html: str) -> set[str]:
    out: set[str] = set()
    for m in CF_EMAIL_RE.finditer(html):
        decoded = decode_cf_email(m.group(1))
        if decoded:
            ne = _norm_email(decoded)
            if ne:
                out.add(ne)
    return out


# ---------------------------------------------------------------------------
# Bot-block detection
# ---------------------------------------------------------------------------

def is_bot_blocked(html: Optional[str], status: int) -> bool:
    if status in (403, 429, 503):
        return True
    if not html:
        return False
    head = html[:5000]
    return any(p.search(head) for p in BOT_BLOCK_PATTERNS)


# ---------------------------------------------------------------------------
# Extracción de emails con etiqueta de fuente
# ---------------------------------------------------------------------------

def _walk_json_for_email(obj: object, found: set[str]) -> None:
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(k, str) and k.lower() in ("email", "e-mail") and isinstance(v, str):
                ne = _norm_email(v)
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
        if blob.count("{") > 1 and "}{" in blob.replace("}\n{", "}{"):
            candidates.extend(part.strip() for part in re.split(r"\}\s*\{", blob) if part.strip())
        for piece in candidates:
            piece = piece.strip()
            if not piece.startswith("{") and not piece.startswith("["):
                continue
            try:
                data = json.loads(piece)
            except json.JSONDecodeError:
                continue
            _walk_json_for_email(data, found)
    return found


def extract_json_kv_emails(html: str) -> set[str]:
    found: set[str] = set()
    for m in JSON_EMAIL_KV.finditer(html):
        ne = _norm_email(m.group(1))
        if ne:
            found.add(ne)
    return found


def extract_obfuscated_emails(html: str) -> set[str]:
    """Detecta emails ofuscados con [at]/(at)/at/&#64; y [dot]/(dot)/dot/&#46;"""
    out: set[str] = set()
    for m in OBFUSC_RE.finditer(html):
        candidate = f"{m.group(1)}@{m.group(2)}.{m.group(3)}"
        ne = _norm_email(candidate)
        if ne:
            out.add(ne)
    return out


def _clean_json_escape_prefix(raw: str) -> str:
    """Quita prefijos JSON-escape como 'u003e' (escape de '>') que se cuelan delante del local-part."""
    if not raw:
        return raw
    local, _, rest = raw.partition("@")
    if not rest:
        return raw
    while local and len(local) >= 4 and JSON_ESCAPE_PREFIX_RE.match(local):
        local = local[4:]
    return f"{local}@{rest}" if local else raw


def extract_emails_with_source(html: str) -> list[tuple[str, str]]:
    """Devuelve [(email, source)] sin duplicar; mantiene la fuente con más confianza."""
    seen: dict[str, str] = {}  # email -> source (primera = mejor por orden de extracción)

    def _add(em: Optional[str], src: str) -> None:
        if em and em not in seen:
            seen[em] = src

    # Orden = prioridad (mejor primero)
    for m in MAILTO_RE.finditer(html):
        _add(_norm_email(_clean_json_escape_prefix(m.group(1))), "mailto")

    for em in extract_cf_emails(html):
        _add(em, "cf_decode")

    for em in extract_ld_json_emails(html):
        _add(em, "ld_json")

    for em in extract_json_kv_emails(html):
        _add(em, "json_kv")

    for em in extract_obfuscated_emails(html):
        _add(em, "obfuscated")

    plain = strip_tags(html)
    for m in EMAIL_RE.finditer(plain):
        _add(_norm_email(_clean_json_escape_prefix(m.group(0))), "plain_text")

    for m in EMAIL_RE.finditer(html):
        s = m.group(0)
        if len(s) > 80:
            continue
        _add(_norm_email(_clean_json_escape_prefix(s)), "html_raw")

    return list(seen.items())


# ---------------------------------------------------------------------------
# DNS MX + SMTP RCPT (verificación real)
# ---------------------------------------------------------------------------

_MX_CACHE: dict[str, list[str]] = {}
_CATCHALL_CACHE: dict[str, bool] = {}


def check_mx(domain: str) -> list[str]:
    if not HAS_DNS:
        return []
    if domain in _MX_CACHE:
        return _MX_CACHE[domain]
    try:
        ans = dns.resolver.resolve(domain, "MX", lifetime=4)
        out = [str(r.exchange).rstrip(".") for r in sorted(ans, key=lambda x: x.preference)]
    except Exception:
        out = []
    _MX_CACHE[domain] = out
    return out


async def smtp_rcpt_async(
    email: str,
    mx_hosts: list[str],
    helo_domain: str = "rcpt-check.local",
    timeout: float = 8.0,
) -> str:
    """Devuelve un código corto auditable: 250_ok / 550_no_mailbox / port25_blocked / timeout / no_mx ..."""
    if not HAS_AIOSMTP:
        return "aiosmtplib_missing"
    if not mx_hosts:
        return "no_mx"
    for mx in mx_hosts[:2]:
        try:
            smtp = aiosmtplib.SMTP(hostname=mx, port=25, timeout=timeout)
            await smtp.connect()
            await smtp.helo(helo_domain)
            await smtp.mail("verify@" + helo_domain)
            code, _ = await smtp.rcpt(email)
            try:
                await smtp.quit()
            except Exception:
                pass
            if code == 250:
                return "250_ok"
            if code in (550, 551, 553, 554):
                return f"{code}_rejected"
            return f"unknown_{code}"
        except asyncio.TimeoutError:
            return "timeout"
        except (aiosmtplib.SMTPServerDisconnected, aiosmtplib.SMTPConnectError):
            continue
        except (ConnectionRefusedError, socket.gaierror, OSError):
            continue
        except Exception as e:
            return f"err_{type(e).__name__}"
    return "port25_blocked_or_unreachable"


async def check_catchall_async(
    domain: str,
    mx_hosts: list[str],
    timeout: float = 8.0,
) -> bool:
    """Probe RCPT con un local inexistente para detectar catch-all."""
    if domain in _CATCHALL_CACHE:
        return _CATCHALL_CACHE[domain]
    if not mx_hosts:
        _CATCHALL_CACHE[domain] = False
        return False
    fake = f"zzz-noexist-{int(time.time()) % 99999}@{domain}"
    status = await smtp_rcpt_async(fake, mx_hosts, timeout=timeout)
    is_catchall = status == "250_ok"
    _CATCHALL_CACHE[domain] = is_catchall
    return is_catchall


# ---------------------------------------------------------------------------
# Trust score
# ---------------------------------------------------------------------------

def email_confidence(
    email: str,
    source: str,
    smtp_status: str,
    mx_ok: bool,
    is_catchall: bool,
) -> int:
    score = SOURCE_BASE_SCORE.get(source, 10)
    if mx_ok:
        score += 10
    if smtp_status == "250_ok":
        score += 15
    elif smtp_status.startswith("550") or smtp_status.startswith("551") or smtp_status.startswith("553") or smtp_status.startswith("554"):
        score -= 30
    if is_catchall:
        score -= 5
    local = email.split("@", 1)[0].lower()
    if local in GENERIC_BUT_USEFUL:
        score -= 15
    return max(0, min(100, score))


# ---------------------------------------------------------------------------
# Rate limiter por dominio (más fino que delay global)
# ---------------------------------------------------------------------------

class PerHostRateLimiter:
    def __init__(self, min_interval: float = 1.5):
        self.min_interval = min_interval
        self._last: dict[str, float] = {}
        self._lock = asyncio.Lock()

    async def wait(self, host: str) -> None:
        async with self._lock:
            loop = asyncio.get_event_loop()
            now = loop.time()
            last = self._last.get(host, 0.0)
            delta = self.min_interval - (now - last)
            self._last[host] = now if delta <= 0 else now + delta
        if delta > 0:
            await asyncio.sleep(delta)


# ---------------------------------------------------------------------------
# Async fetch con backoff
# ---------------------------------------------------------------------------

@dataclass
class FetchResult:
    url: str
    status: int
    html: Optional[str]
    error: Optional[str]
    bot_blocked: bool = False


async def fetch_once(
    session: aiohttp.ClientSession,
    url: str,
    sem: asyncio.Semaphore,
    rate_limiter: PerHostRateLimiter,
    timeout_s: float,
) -> FetchResult:
    host = urllib.parse.urlsplit(url).netloc
    async with sem:
        await rate_limiter.wait(host)
        try:
            timeout = aiohttp.ClientTimeout(total=timeout_s, connect=max(2.0, timeout_s / 2))
            async with session.get(url, timeout=timeout, allow_redirects=True) as r:
                status = r.status
                raw = await r.content.read(2_000_000)
                ctype = r.charset or "utf-8"
                try:
                    text = raw.decode(ctype, errors="replace")
                except LookupError:
                    text = raw.decode("utf-8", errors="replace")
                blocked = is_bot_blocked(text, status)
                if status == 200 and not blocked:
                    return FetchResult(url=url, status=status, html=text, error=None, bot_blocked=False)
                return FetchResult(
                    url=url,
                    status=status,
                    html=text if blocked else None,
                    error=f"status_{status}",
                    bot_blocked=blocked,
                )
        except asyncio.TimeoutError:
            return FetchResult(url=url, status=0, html=None, error="timeout", bot_blocked=False)
        except aiohttp.ClientError as e:
            return FetchResult(url=url, status=0, html=None, error=f"client_{type(e).__name__}", bot_blocked=False)
        except Exception as e:
            return FetchResult(url=url, status=0, html=None, error=f"err_{type(e).__name__}", bot_blocked=False)


_CS_SCRAPER = None
_CS_FALLBACK_ENABLED = True


def _get_cloudscraper():
    global _CS_SCRAPER
    if not HAS_CLOUDSCRAPER:
        return None
    if _CS_SCRAPER is None:
        try:
            _CS_SCRAPER = cloudscraper.create_scraper(
                browser={"browser": "chrome", "platform": "darwin", "desktop": True}
            )
        except Exception:
            _CS_SCRAPER = False
    return _CS_SCRAPER if _CS_SCRAPER else None


def _cs_fetch_sync(url: str, timeout_s: float) -> FetchResult:
    """Sync cloudscraper fetch. Run via asyncio.to_thread()."""
    scraper = _get_cloudscraper()
    if not scraper:
        return FetchResult(url=url, status=0, html=None, error="cs_unavailable", bot_blocked=False)
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,es;q=0.8",
        "Cache-Control": "no-cache",
    }
    try:
        r = scraper.get(url, headers=headers, timeout=timeout_s, allow_redirects=True)
        text = r.text
        status = r.status_code
        blocked = is_bot_blocked(text, status)
        if status == 200 and not blocked:
            return FetchResult(url=url, status=status, html=text, error=None, bot_blocked=False)
        return FetchResult(
            url=url,
            status=status,
            html=text if blocked else None,
            error=f"cs_status_{status}",
            bot_blocked=blocked,
        )
    except Exception as e:
        return FetchResult(url=url, status=0, html=None, error=f"cs_err_{type(e).__name__}", bot_blocked=False)


def _looks_anti_bot_short(html: Optional[str], url: str) -> bool:
    """Detecta HTML 'placeholder' que algunos hosts (Wix, etc.) sirven a clientes no-browser.
    Marker típico: status 200 pero body < 3000 chars o sin tag <body>."""
    if not html:
        return False
    if len(html) < 3000:
        return True
    low = html.lower()
    if "<body" not in low and "<main" not in low:
        return True
    return False


async def fetch_with_backoff(
    session: aiohttp.ClientSession,
    url: str,
    sem: asyncio.Semaphore,
    rate_limiter: PerHostRateLimiter,
    timeout_s: float,
    max_retries: int = 2,
    use_cs_fallback: bool = True,
) -> FetchResult:
    delay = 1.0
    last: Optional[FetchResult] = None
    for attempt in range(max_retries + 1):
        last = await fetch_once(session, url, sem, rate_limiter, timeout_s)
        if last.html and not last.bot_blocked and not _looks_anti_bot_short(last.html, url):
            return last
        if last.status in (429, 503):
            await asyncio.sleep(delay + (attempt * 0.5))
            delay *= 2
            continue
        break

    short_html_trigger = last and last.html and _looks_anti_bot_short(last.html, url)

    if use_cs_fallback and _CS_FALLBACK_ENABLED and HAS_CLOUDSCRAPER and last and (
        last.bot_blocked
        or last.status in (403, 429, 503)
        or short_html_trigger
        or (
            last.status == 0
            and last.error
            and any(
                tag in last.error
                for tag in ("client_", "timeout", "err_TimeoutError", "err_ClientConnector")
            )
        )
    ):
        cs_result = await asyncio.to_thread(_cs_fetch_sync, url, timeout_s + 4.0)
        if cs_result.html and not cs_result.bot_blocked and not _looks_anti_bot_short(cs_result.html, url):
            return cs_result
        if cs_result.html and last and (not last.html or len(cs_result.html) > len(last.html) * 2):
            return cs_result

    return last  # type: ignore[return-value]


async def fetch_first_ok(
    session: aiohttp.ClientSession,
    base_url: str,
    sem: asyncio.Semaphore,
    rate_limiter: PerHostRateLimiter,
    timeout_s: float,
) -> FetchResult:
    last: Optional[FetchResult] = None
    variants = url_variants(base_url)
    for idx, u in enumerate(variants):
        res = await fetch_with_backoff(
            session, u, sem, rate_limiter, timeout_s,
            use_cs_fallback=(idx == 0),
        )
        last = res
        if res.html and not res.bot_blocked:
            return res
    return last  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# Sitemap discovery
# ---------------------------------------------------------------------------

async def discover_priority_urls(
    session: aiohttp.ClientSession,
    base_url: str,
    sem: asyncio.Semaphore,
    rate_limiter: PerHostRateLimiter,
    timeout_s: float,
    max_extra: int = 8,
) -> list[str]:
    found: list[str] = []
    for sp in SITEMAP_PATHS:
        sm_url = urllib.parse.urljoin(base_url.rstrip("/") + "/", sp.lstrip("/"))
        res = await fetch_once(session, sm_url, sem, rate_limiter, timeout_s)
        if not res.html:
            continue
        for m in re.finditer(r"<loc>([^<]+)</loc>", res.html):
            loc = m.group(1).strip()
            if any(tok in loc.lower() for tok in PRIORITY_TOKENS):
                if loc not in found:
                    found.append(loc)
                    if len(found) >= max_extra:
                        return found
    return found


# ---------------------------------------------------------------------------
# LLM extraction (opcional) — nombre + cargo desde chunk con email
# ---------------------------------------------------------------------------

_LLM_CLIENT: Optional[object] = None


def _llm_client() -> Optional[object]:
    global _LLM_CLIENT
    if _LLM_CLIENT is not None:
        return _LLM_CLIENT
    if not HAS_OPENAI:
        return None
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    try:
        _LLM_CLIENT = OpenAI(api_key=api_key)
        return _LLM_CLIENT
    except Exception:
        return None


def _llm_extract_name_title(snippet: str, email: str) -> tuple[str, str]:
    client = _llm_client()
    if client is None:
        return "", ""
    snippet = (snippet or "")[:1200]
    try:
        resp = client.chat.completions.create(  # type: ignore[attr-defined]
            model=os.getenv("VANGUARD_LLM_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": LLM_EXTRACT_PROMPT},
                {"role": "user", "content": f"Email: {email}\n\nSnippet:\n{snippet}"},
            ],
            temperature=0,
            max_tokens=120,
            response_format={"type": "json_object"},
        )
        content = resp.choices[0].message.content or "{}"
        data = json.loads(content)
        return (data.get("name") or "").strip(), (data.get("title") or "").strip()
    except Exception:
        return "", ""


def _snippet_around_email(html: str, email: str, radius: int = 400) -> str:
    plain = strip_tags(html)
    idx = plain.lower().find(email.lower())
    if idx == -1:
        return plain[:radius * 2]
    start = max(0, idx - radius)
    end = min(len(plain), idx + len(email) + radius)
    return plain[start:end]


# ---------------------------------------------------------------------------
# Lectura / escritura CSV
# ---------------------------------------------------------------------------

OUT_FIELDS = [
    "email",
    "company",
    "website",
    "phone",
    "city",
    "state",
    "country",
    "google_maps_url",
    "lead_score",
    "email_source",
    "email_source_url",
    "mx_ok",
    "smtp_status",
    "is_catchall",
    "confidence",
    "person_name",
    "person_title",
    "pages_tried",
    "pages_ok",
    "bot_blocked",
    "errors",
]


def read_prep(path: Path, sep: str) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        r = csv.DictReader(f, delimiter=sep)
        return [dict(row) for row in r]


def score_row(row: dict[str, str]) -> int:
    try:
        return int(float(row.get("lead_score") or 0))
    except (TypeError, ValueError):
        return 0


def row_to_out(
    ne: str,
    row: dict[str, str],
    website: str,
    source: str,
    source_url: str,
    mx_ok: bool,
    smtp_status: str,
    is_catchall: bool,
    confidence: int,
    person_name: str = "",
    person_title: str = "",
    pages_tried: int = 0,
    pages_ok: int = 0,
    bot_blocked: bool = False,
    errors: str = "",
) -> dict[str, str]:
    return {
        "email": ne,
        "company": (row.get("company_name") or "").strip(),
        "website": website,
        "phone": (row.get("phone") or "").strip(),
        "city": (row.get("city") or "").strip(),
        "state": (row.get("state") or "").strip(),
        "country": (row.get("country") or "").strip(),
        "google_maps_url": (row.get("google_maps_url") or "").strip(),
        "lead_score": str(score_row(row)),
        "email_source": source,
        "email_source_url": source_url,
        "mx_ok": "1" if mx_ok else "0",
        "smtp_status": smtp_status,
        "is_catchall": "1" if is_catchall else "0",
        "confidence": str(confidence),
        "person_name": person_name,
        "person_title": person_title,
        "pages_tried": str(pages_tried),
        "pages_ok": str(pages_ok),
        "bot_blocked": "1" if bot_blocked else "0",
        "errors": errors,
    }


def load_done_websites(output_path: Path) -> set[str]:
    done: set[str] = set()
    if not output_path.is_file():
        return done
    try:
        with output_path.open("r", encoding="utf-8-sig", newline="") as f:
            r = csv.DictReader(f)
            for row in r:
                w = (row.get("website") or "").strip()
                if w:
                    done.add(w)
    except Exception:
        return done
    return done


# ---------------------------------------------------------------------------
# Crawl por sitio (compone CONTACT_PATHS + sitemap, paralelo interno)
# ---------------------------------------------------------------------------

@dataclass
class SiteCrawlResult:
    website: str
    emails_with_source: dict[str, tuple[str, str]] = field(default_factory=dict)
    # email -> (source_tag, source_url)
    bot_blocked: bool = False
    errors: list[str] = field(default_factory=list)
    raw_html_by_url: dict[str, str] = field(default_factory=dict)
    pages_tried: int = 0
    pages_ok: int = 0


async def crawl_site(
    session: aiohttp.ClientSession,
    entry_url: str,
    sem: asyncio.Semaphore,
    rate_limiter: PerHostRateLimiter,
    timeout_s: float,
    max_paths: int,
    use_sitemap: bool,
) -> SiteCrawlResult:
    result = SiteCrawlResult(website=entry_url)

    paths = list(CONTACT_PATHS[: max(1, max_paths)])
    urls: list[str] = []
    for p in paths:
        urls.append(join_url(entry_url, p) if p else entry_url)

    if use_sitemap:
        try:
            extra = await discover_priority_urls(session, entry_url, sem, rate_limiter, timeout_s)
            for u in extra:
                if u not in urls:
                    urls.append(u)
        except Exception as e:  # noqa: BLE001
            result.errors.append(f"sitemap_err_{type(e).__name__}")

    fetch_tasks = [fetch_first_ok(session, u, sem, rate_limiter, timeout_s) for u in urls]
    fetched = await asyncio.gather(*fetch_tasks, return_exceptions=True)
    result.pages_tried = len(fetch_tasks)

    for res in fetched:
        if isinstance(res, Exception):
            result.errors.append(f"gather_{type(res).__name__}")
            continue
        if res.bot_blocked:
            result.bot_blocked = True
        if not res.html:
            if res.error:
                result.errors.append(res.error)
            continue
        result.pages_ok += 1
        result.raw_html_by_url[res.url] = res.html
        for em, src in extract_emails_with_source(res.html):
            if em not in result.emails_with_source:
                result.emails_with_source[em] = (src, res.url)

    return result


# ---------------------------------------------------------------------------
# Main async
# ---------------------------------------------------------------------------

async def main_async(args: argparse.Namespace) -> int:
    global _CS_FALLBACK_ENABLED
    _CS_FALLBACK_ENABLED = not getattr(args, "no_cloudscraper_fallback", False)
    if _CS_FALLBACK_ENABLED and HAS_CLOUDSCRAPER:
        print("[i] cloudscraper fallback: ENABLED (kicks in on 403/429/503/bot-blocked)")
    elif _CS_FALLBACK_ENABLED and not HAS_CLOUDSCRAPER:
        print("[!] cloudscraper not installed → fallback DISABLED. `pip install cloudscraper` to enable.")
    else:
        print("[i] cloudscraper fallback: DISABLED (via --no-cloudscraper-fallback)")

    rows = read_prep(args.input_csv, args.sep)

    by_site: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        w = canonicalize_website(row.get("website", "") or "")
        if w and not should_skip_url(w, args.include_social):
            by_site[w].append(row)

    done_sites = load_done_websites(args.output) if args.resume else set()
    sites_to_process = [s for s in sorted(by_site.keys()) if s not in done_sites]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    mode = "a" if (args.resume and args.output.exists()) else "w"
    out_f = args.output.open(mode, encoding="utf-8-sig", newline="")
    writer = csv.DictWriter(out_f, fieldnames=OUT_FIELDS, extrasaction="ignore")
    if mode == "w":
        writer.writeheader()
        out_f.flush()

    log_path: Optional[Path] = None
    log_f = None
    if args.jsonl_log:
        log_path = args.output.parent / f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
        log_f = log_path.open("w", encoding="utf-8")

    sem = asyncio.Semaphore(args.concurrency)
    rate_limiter = PerHostRateLimiter(min_interval=args.delay)

    ua = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    )
    headers = {
        "User-Agent": ua,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "es-EC,es;q=0.9,en;q=0.8",
        "Accept-Encoding": "identity",
        "Cache-Control": "no-cache",
    }
    connector = aiohttp.TCPConnector(
        limit=args.concurrency,
        ttl_dns_cache=300,
        ssl=ssl.create_default_context() if args.verify_ssl else False,
    )

    best_for_email: dict[str, tuple[int, dict[str, str]]] = {}

    def upsert(em: str, out_row: dict[str, str], sc: int) -> None:
        prev = best_for_email.get(em)
        if prev is None or sc > prev[0]:
            best_for_email[em] = (sc, out_row)

    total = len(sites_to_process)
    print(
        f"Webs únicos a rastrear: {total} "
        f"(saltando {len(done_sites)} ya en output)\n"
        f"  concurrency={args.concurrency} timeout={args.timeout}s delay={args.delay}s "
        f"check_smtp={args.check_smtp} use_sitemap={args.use_sitemap} use_llm={args.use_llm}",
        file=sys.stderr,
    )

    async with aiohttp.ClientSession(connector=connector, headers=headers) as session:
        for i, site in enumerate(sites_to_process, start=1):
            t0 = time.time()
            row_candidates = by_site[site]
            best_row = max(row_candidates, key=score_row)
            sc = score_row(best_row)

            if args.skip_crawl:
                site_emails: dict[str, tuple[str, str]] = {}
                bot_blocked = False
                errors: list[str] = []
                raw_html_by_url: dict[str, str] = {}
                pages_tried = 0
                pages_ok = 0
            else:
                cr = await crawl_site(
                    session, site, sem, rate_limiter, args.timeout, args.max_paths, args.use_sitemap
                )
                site_emails = cr.emails_with_source
                bot_blocked = cr.bot_blocked
                errors = cr.errors
                raw_html_by_url = cr.raw_html_by_url
                pages_tried = cr.pages_tried
                pages_ok = cr.pages_ok

            errors_str = ";".join(errors[:6]) if errors else ""

            # Incluye email del CSV original si existe
            existing = (best_row.get("email") or "").strip()
            if existing and "@" in existing:
                ne = _norm_email(existing)
                if ne and ne not in site_emails:
                    site_emails[ne] = ("csv_original", site)

            # Verificación + LLM por email
            for em, (src, src_url) in site_emails.items():
                domain = em.split("@", 1)[1]
                mx_ok = False
                smtp_status = "skipped"
                is_catchall = False

                if args.check_smtp:
                    mx = check_mx(domain)
                    mx_ok = bool(mx)
                    if mx_ok and not args.skip_smtp_probe:
                        smtp_status = await smtp_rcpt_async(em, mx, timeout=args.smtp_timeout)
                        if smtp_status == "250_ok":
                            is_catchall = await check_catchall_async(domain, mx, timeout=args.smtp_timeout)
                    elif mx_ok and args.skip_smtp_probe:
                        smtp_status = "port25_skipped"

                conf = email_confidence(em, src, smtp_status, mx_ok, is_catchall)

                person_name = ""
                person_title = ""
                if args.use_llm and raw_html_by_url:
                    chosen_html = raw_html_by_url.get(src_url) or next(iter(raw_html_by_url.values()))
                    snippet = _snippet_around_email(chosen_html, em)
                    person_name, person_title = _llm_extract_name_title(snippet, em)

                out_row = row_to_out(
                    em, best_row, site, src, src_url,
                    mx_ok, smtp_status, is_catchall, conf,
                    person_name=person_name, person_title=person_title,
                    pages_tried=pages_tried, pages_ok=pages_ok,
                    bot_blocked=bot_blocked, errors=errors_str,
                )

                if args.stream_output:
                    writer.writerow(out_row)
                    out_f.flush()
                else:
                    upsert(em, out_row, sc)

            elapsed_ms = int((time.time() - t0) * 1000)
            tag = " (bot-blocked)" if bot_blocked else ""
            print(
                f"[{i}/{total}] {site} -> {len(site_emails)} emails {elapsed_ms}ms{tag}",
                file=sys.stderr,
            )
            if log_f is not None:
                log_f.write(
                    json.dumps(
                        {
                            "ts": datetime.now().isoformat(),
                            "website": site,
                            "emails_found": len(site_emails),
                            "bot_blocked": bot_blocked,
                            "elapsed_ms": elapsed_ms,
                            "errors": errors[:5],
                        }
                    )
                    + "\n"
                )
                log_f.flush()

        # Filas extra con email pero sin website crawled (p. ej. solo IG en CSV)
        for row in rows:
            ne = _norm_email((row.get("email") or "").strip())
            if not ne:
                continue
            w = canonicalize_website(row.get("website", "") or "") or ""
            domain = ne.split("@", 1)[1]
            mx_ok = False
            smtp_status = "skipped"
            is_catchall = False
            if args.check_smtp:
                mx = check_mx(domain)
                mx_ok = bool(mx)
                if mx_ok and not args.skip_smtp_probe:
                    smtp_status = await smtp_rcpt_async(ne, mx, timeout=args.smtp_timeout)
                    if smtp_status == "250_ok":
                        is_catchall = await check_catchall_async(domain, mx, timeout=args.smtp_timeout)
                elif mx_ok and args.skip_smtp_probe:
                    smtp_status = "port25_skipped"

            conf = email_confidence(ne, "csv_row", smtp_status, mx_ok, is_catchall)
            out_row = row_to_out(
                ne, row, w, "csv_row", w, mx_ok, smtp_status, is_catchall, conf
            )
            sc = score_row(row)
            if args.stream_output:
                writer.writerow(out_row)
                out_f.flush()
            else:
                upsert(ne, out_row, sc)

    if not args.stream_output:
        # Orden final: confidence DESC, lead_score DESC, email ASC
        out_rows = [
            t[1]
            for t in sorted(
                best_for_email.values(),
                key=lambda x: (-int(x[1]["confidence"]), -x[0], x[1]["email"]),
            )
        ]
        for r in out_rows:
            writer.writerow(r)

    out_f.close()
    if log_f is not None:
        log_f.close()
        print(f"  JSONL log: {log_path}", file=sys.stderr)

    total_emails = len(best_for_email) if not args.stream_output else "(stream — ver CSV)"
    print(
        f"Listo: {args.output}\n"
        f"  filas CSV entrada: {len(rows)}\n"
        f"  websites procesados: {total}\n"
        f"  emails únicos: {total_emails}",
        file=sys.stderr,
    )
    return 0


# ---------------------------------------------------------------------------
# Argparse + entrypoint
# ---------------------------------------------------------------------------

def build_argparser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="V4 async + SMTP verify + CF decode + trust score. Honest deliverability per row.",
    )
    ap.add_argument("input_csv", type=Path)
    ap.add_argument("-o", "--output", type=Path, required=True)
    ap.add_argument("--sep", default=";", help="Separador del CSV de entrada (default ;).")
    ap.add_argument("--delay", type=float, default=1.5, help="Min segundos entre hits al mismo dominio.")
    ap.add_argument("--timeout", type=float, default=8.0, help="Timeout total por request HTTP.")
    ap.add_argument("--include-social", action="store_true")
    ap.add_argument("--max-paths", type=int, default=6)
    ap.add_argument("--skip-crawl", action="store_true", help="Solo normaliza emails del CSV (sin HTTP).")
    ap.add_argument(
        "--no-cloudscraper-fallback",
        action="store_true",
        help="Desactiva el fallback a cloudscraper cuando aiohttp es bot-blocked (default: activo si instalado).",
    )
    ap.add_argument("--concurrency", type=int, default=20, help="Máx requests HTTP en paralelo.")
    ap.add_argument("--check-smtp", action="store_true", help="MX + SMTP RCPT real-time por email.")
    ap.add_argument(
        "--skip-smtp-probe",
        action="store_true",
        help="Hace MX pero no RCPT (ISP residencial suele bloquear puerto 25).",
    )
    ap.add_argument("--smtp-timeout", type=float, default=8.0)
    ap.add_argument("--use-sitemap", action="store_true", help="Descubre URLs contacto/team vía sitemap.xml.")
    ap.add_argument("--use-llm", action="store_true", help="Extrae nombre+cargo con gpt-4o-mini cerca del email.")
    ap.add_argument("--resume", action="store_true", help="Salta websites ya escritos en el output CSV.")
    ap.add_argument(
        "--stream-output",
        action="store_true",
        help="Escribe filas a medida que se procesan (recomendado para corridas largas / --resume).",
    )
    ap.add_argument("--jsonl-log", action="store_true", help="Genera log JSONL por sitio en la carpeta del output.")
    ap.add_argument("--verify-ssl", action="store_true", help="Verifica certificados SSL (default: off para más recall).")
    return ap


def main() -> int:
    args = build_argparser().parse_args()
    if not args.input_csv.is_file():
        print(f"Error: no existe {args.input_csv}", file=sys.stderr)
        return 1

    if args.check_smtp and not HAS_DNS:
        print(
            "Aviso: dnspython no instalado; --check-smtp requiere `pip install dnspython`. "
            "Deshabilitando verificación SMTP.",
            file=sys.stderr,
        )
        args.check_smtp = False
    if args.check_smtp and not args.skip_smtp_probe and not HAS_AIOSMTP:
        print(
            "Aviso: aiosmtplib no instalado; SMTP RCPT requiere `pip install aiosmtplib`. "
            "Solo MX check estará disponible.",
            file=sys.stderr,
        )
        args.skip_smtp_probe = True
    if args.use_llm and not HAS_OPENAI:
        print(
            "Aviso: openai no instalado; --use-llm requiere `pip install openai`. "
            "Desactivando LLM extraction.",
            file=sys.stderr,
        )
        args.use_llm = False
    if args.use_llm and not os.getenv("OPENAI_API_KEY"):
        print("Aviso: OPENAI_API_KEY no seteado; desactivando --use-llm.", file=sys.stderr)
        args.use_llm = False

    return asyncio.run(main_async(args))


if __name__ == "__main__":
    raise SystemExit(main())
