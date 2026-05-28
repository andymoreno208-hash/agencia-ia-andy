from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urljoin, urlsplit, urlunsplit

import aiohttp

from .config import RadarConfig
from .extract_html import extract_emails_with_context
from .hygiene import canonicalize_website, norm_email, should_skip_url

CONTACT_PATHS = (
    "", "/contact", "/contact/", "/contacto", "/contacto/", "/contacts",
    "/es/contacto", "/en/contact", "/about", "/nosotros",
)


@dataclass
class EmailHit:
    email: str
    context: str
    source_url: str
    row: dict[str, Any] = field(default_factory=dict)
    website: str = ""


def _url_variants(url: str) -> list[str]:
    p = urlsplit(url)
    hosts = [p.netloc]
    if p.netloc.startswith("www."):
        bare = p.netloc[4:]
        if bare:
            hosts.append(bare)
    else:
        hosts.append("www." + p.netloc)
    out: list[str] = []
    seen: set[str] = set()
    for h in hosts:
        for sch in ("https", "http"):
            u = urlunsplit((sch, h, p.path or "/", p.query, ""))
            if u not in seen:
                seen.add(u)
                out.append(u)
    return out


def _join_url(base: str, path: str) -> str:
    if not path:
        return base
    return urljoin(base.rstrip("/") + "/", path.lstrip("/"))


def normalize_apify_row(item: dict[str, Any]) -> dict[str, Any]:
    """Mapea campos típicos Apify Maps / genéricos a schema interno."""
    website = (
        item.get("website")
        or item.get("url")
        or item.get("domain")
        or ""
    )
    if website and not str(website).startswith("http"):
        website = "https://" + str(website).lstrip("/")
    return {
        "company_name": item.get("title") or item.get("company_name") or item.get("name") or "",
        "website": website,
        "email": item.get("email") or "",
        "phone": item.get("phone") or item.get("phoneNumber") or "",
        "city": item.get("city") or "",
        "state": item.get("state") or item.get("stateCode") or "",
        "country": item.get("country") or item.get("countryCode") or "",
        "google_maps_url": item.get("url") or item.get("placeUrl") or "",
        "lead_score": str(item.get("lead_score") or item.get("totalScore") or ""),
        "_raw": item,
    }


async def _fetch_html(
    session: aiohttp.ClientSession,
    url: str,
    cfg: RadarConfig,
) -> tuple[str | None, str | None]:
    headers = {
        "User-Agent": cfg.user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "es-EC,es;q=0.9,en;q=0.8",
        "Cache-Control": "no-cache",
    }
    last_err: str | None = None
    for u in _url_variants(url):
        try:
            async with session.get(
                u,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=cfg.http_timeout),
                allow_redirects=True,
            ) as resp:
                if resp.status >= 400:
                    last_err = f"HTTP {resp.status}"
                    continue
                raw = await resp.content.read(2_000_000)
                ctype = resp.charset or "utf-8"
                try:
                    return raw.decode(ctype, errors="replace"), None
                except LookupError:
                    return raw.decode("utf-8", errors="replace"), None
        except (aiohttp.ClientError, asyncio.TimeoutError, OSError) as e:
            last_err = str(e)[:220]
    return None, last_err


async def _crawl_one_site(
    session: aiohttp.ClientSession,
    sem: asyncio.Semaphore,
    site: str,
    rows: list[dict[str, Any]],
    cfg: RadarConfig,
    cache: dict[str, list[EmailHit]],
) -> list[EmailHit]:
    if site in cache:
        return cache[site]

    async with sem:
        hits: list[EmailHit] = []
        def _score(r: dict[str, Any]) -> int:
            try:
                return int(float(r.get("lead_score") or 0))
            except (TypeError, ValueError):
                return 0

        best_row = max(rows, key=_score)
        paths = CONTACT_PATHS[: max(1, cfg.max_contact_paths)]
        url_cache: dict[str, str | None] = {}

        for path in paths:
            u = _join_url(site, path) if path else site
            if u in url_cache:
                html = url_cache[u]
            else:
                html, _ = await _fetch_html(session, u, cfg)
                url_cache[u] = html
            if not html:
                continue
            for email, ctx in extract_emails_with_context(html):
                hits.append(
                    EmailHit(
                        email=email,
                        context=ctx,
                        source_url=u,
                        row=best_row,
                        website=site,
                    )
                )

        # Email ya en fila Apify/CSV
        for row in rows:
            ne = norm_email(str(row.get("email") or ""))
            if ne:
                hits.append(
                    EmailHit(
                        email=ne,
                        context=ne,
                        source_url=site,
                        row=row,
                        website=site,
                    )
                )

        cache[site] = hits
        return hits


async def crawl_all_rows(
    rows: list[dict[str, Any]],
    cfg: RadarConfig,
) -> list[EmailHit]:
    by_site: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        w = canonicalize_website(str(row.get("website") or ""))
        if not w or should_skip_url(w, cfg.include_social):
            ne = norm_email(str(row.get("email") or ""))
            if ne:
                by_site.setdefault("", []).append(row)
            continue
        by_site.setdefault(w, []).append(row)

    sem = asyncio.Semaphore(cfg.http_concurrency)
    cache: dict[str, list[EmailHit]] = {}
    connector = aiohttp.TCPConnector(limit=cfg.http_concurrency, ssl=False)

    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [
            _crawl_one_site(session, sem, site, site_rows, cfg, cache)
            for site, site_rows in by_site.items()
            if site
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    all_hits: list[EmailHit] = []
    for i, res in enumerate(results):
        if isinstance(res, Exception):
            site = list(by_site.keys())[i] if i < len(by_site) else "?"
            print(f"[crawl] error {site}: {res}")
            continue
        all_hits.extend(res)

    # Filas solo con email sin website
    for row in by_site.get("", []):
        ne = norm_email(str(row.get("email") or ""))
        if ne:
            all_hits.append(
                EmailHit(email=ne, context=ne, source_url="", row=row, website="")
            )

    # Dedupe por email — conserva mayor contexto
    best: dict[str, EmailHit] = {}
    for h in all_hits:
        prev = best.get(h.email)
        if prev is None or len(h.context) > len(prev.context):
            best[h.email] = h
    print(f"[crawl] {len(by_site)} sitios → {len(best)} emails únicos")
    return list(best.values())
