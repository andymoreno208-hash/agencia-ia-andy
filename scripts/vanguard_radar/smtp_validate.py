from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass

import dns.resolver
from aiosmtplib import SMTP

from .config import RadarConfig
from .llm_extract import EnrichedLead

SMTP_OK = re.compile(r"^2\d{2}\b")
SMTP_BAD = re.compile(r"^(550|551|552|553|554)\b")


@dataclass
class SmtpResult:
    email: str
    valid: bool
    detail: str
    mx_host: str = ""


def _mx_hosts(domain: str) -> list[str]:
    try:
        answers = dns.resolver.resolve(domain, "MX")
        pairs = sorted((r.preference, str(r.exchange).rstrip(".")) for r in answers)
        return [h for _, h in pairs]
    except Exception as e:
        return []


async def _verify_on_mx(
    email: str,
    mx_host: str,
    cfg: RadarConfig,
) -> SmtpResult:
    local, _, domain = email.partition("@")
    if not local or not domain:
        return SmtpResult(email, False, "malformed")

    try:
        smtp = SMTP(hostname=mx_host, port=25, timeout=cfg.smtp_timeout, use_tls=False)
        await smtp.connect()
        await smtp.ehlo(cfg.smtp_helo)
        await smtp.mail(cfg.smtp_mail_from)
        code, msg = await smtp.rcpt(email)
        await smtp.quit()

        reply = f"{code} {msg}".strip() if msg else str(code)
        code_s = str(code)
        if SMTP_OK.match(code_s) or code_s.startswith("2"):
            return SmtpResult(email, True, reply, mx_host)
        if SMTP_BAD.match(code_s) or code_s.startswith(("550", "551", "552", "553", "554")):
            return SmtpResult(email, False, reply, mx_host)
        # 4xx greylisting — tratar como no verificado
        return SmtpResult(email, False, f"inconclusive:{reply}", mx_host)
    except Exception as e:
        return SmtpResult(email, False, f"error:{e!s}"[:200], mx_host)


async def verify_email_smtp(email: str, cfg: RadarConfig) -> SmtpResult:
    domain = email.split("@", 1)[-1].lower()
    hosts = _mx_hosts(domain)
    if not hosts:
        return SmtpResult(email, False, "no_mx")

    last = SmtpResult(email, False, "all_mx_failed")
    for mx in hosts[:3]:
        res = await _verify_on_mx(email, mx, cfg)
        if res.valid:
            return res
        if res.detail.startswith(("550", "551", "552", "553", "554")) or "550" in res.detail:
            return res
        last = res
    return last


async def filter_deliverable(
    leads: list[EnrichedLead],
    cfg: RadarConfig,
) -> tuple[list[EnrichedLead], list[SmtpResult]]:
    if cfg.skip_smtp:
        print("[smtp] SKIP — todos pasan (solo QA local; no vender como zero-bounce)")
        return leads, []

    sem = asyncio.Semaphore(cfg.smtp_concurrency)
    results: list[SmtpResult] = []

    async def one(lead: EnrichedLead) -> tuple[EnrichedLead, SmtpResult]:
        async with sem:
            r = await verify_email_smtp(lead.email, cfg)
            return lead, r

    pairs = await asyncio.gather(*[one(ld) for ld in leads])
    ok_leads: list[EnrichedLead] = []
    for lead, r in pairs:
        results.append(r)
        if r.valid:
            ok_leads.append(lead)
        else:
            print(f"[smtp] reject {lead.email} — {r.detail}")

    print(f"[smtp] {len(ok_leads)}/{len(leads)} pasaron RCPT")
    return ok_leads, results
