from __future__ import annotations

import re
from urllib.parse import urlsplit, urlunsplit

EMAIL_RE = re.compile(
    r"[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@"
    r"[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?"
    r"(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)+",
    re.IGNORECASE,
)

GENERIC_LOCAL = frozenset(
    {
        "noreply", "no-reply", "donotreply", "mailer-daemon", "postmaster",
        "webmaster", "hostmaster", "abuse", "privacy", "legal", "newsletter",
        "news", "bounce", "mail", "info", "contact", "hello", "support",
        "admin", "office", "sales", "ventas", "marketing",
    }
)

PLACEHOLDER_DOMAINS = frozenset(
    {"example.com", "test.com", "localhost", "sentry.io", "wixpress.com"}
)

SKIP_HOST_SUBSTRINGS = (
    "instagram.com", "facebook.com", "fb.com", "tiktok.com", "twitter.com",
    "x.com", "linkedin.com", "youtube.com", "youtu.be", "wa.me",
    "maps.google", "google.com/maps", "goo.gl", "g.co",
)


def norm_email(raw: str) -> str | None:
    e = (raw or "").strip().strip('"').strip("'").rstrip(".,);")
    if "@" not in e:
        return None
    el = e.lower()
    if el.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg")):
        return None
    if not EMAIL_RE.fullmatch(el):
        return None
    local, _, domain = el.partition("@")
    if domain in PLACEHOLDER_DOMAINS or any(domain.endswith("." + p) for p in PLACEHOLDER_DOMAINS):
        return None
    if local in GENERIC_LOCAL:
        return None
    return el


def should_skip_url(url: str, include_social: bool) -> bool:
    if not url or not url.startswith(("http://", "https://")):
        return True
    if include_social:
        return False
    low = url.lower()
    return any(s in low for s in SKIP_HOST_SUBSTRINGS)


def canonicalize_website(raw: str) -> str | None:
    s = (raw or "").strip().strip('"')
    if not s:
        return None
    if s.startswith("//"):
        s = "https:" + s
    if not s.startswith("http"):
        s = "https://" + s
    parts = urlsplit(s)
    if not parts.netloc:
        return None
    return urlunsplit((parts.scheme or "https", parts.netloc, parts.path or "/", parts.query, ""))
