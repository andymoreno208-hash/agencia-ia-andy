#!/usr/bin/env python3
import re
import sys
import time
import random
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urljoin, urlparse

import pandas as pd
import requests
from bs4 import BeautifulSoup

EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I)
SHEET = "Sheet1"

GENERIC_LOCALPART_RE = re.compile(
    r"^(info|office|admin|administration|admissions|admission|enroll|enrollment|contact|hello|help|support|"
    r"attendance|registrar|reception|frontdesk|front\.?desk|school|mail|general|inquiries|"
    r"principal|pastor|headmaster|superintendent|president|director|head|"
    r"finance|businessoffice|business\.office|accounts|accounting|ar|ap|billing|payroll|hr|humanresources|"
    r"it|webmaster|noreply|no-reply|donotreply|donot-reply)(\b|\d|\.|_|-)",
    re.I,
)

# Correos funcionales permitidos SOLO si el contexto confirma rol decisor
HIGH_VALUE_ROLE_LOCALPARTS: set[str] = {
    "principal", "head", "headmaster", "superintendent", "president",
    "cfo", "bursar", "businessmanager", "business.manager",
    "business-office", "businessoffice", "finance", "director",
}

PERSONALISH_RE = re.compile(r"^[a-z0-9]+([._-][a-z0-9]+)+$|^[a-z]{5,}[a-z0-9]*$", re.I)

ROLE_PATTERNS = [
    (re.compile(r"\bchief\s+financial\s+officer\b|\bcfo\b", re.I), 100),
    (re.compile(r"\bdirector\s+of\s+finance\b|\bfinance\s+director\b|\bfinance\b.*\bdirector\b", re.I), 92),
    (re.compile(r"\bbusiness\s+manager\b", re.I), 90),
    (re.compile(r"\bbursar\b", re.I), 86),
    (re.compile(r"\bhead\s+of\s+school\b", re.I), 82),
    (re.compile(r"\bprincipal\b", re.I), 80),
    (re.compile(r"\binterim\s+principal\b", re.I), 80),
    (re.compile(r"\bdirector\s+of\s+operations\b|\boperations\s+director\b", re.I), 70),
    (re.compile(r"\bdirector\b", re.I), 65),
]

# URLs bloqueadas por Cloudflare (no se pueden scrapear desde aquí)
BLOCKED_HOSTS = {
    "santaclaraacademy.org", "www.santaclaraacademy.org", "sites.ecatholic.com",
}

PRIORITY_URL_HINTS = [
    "faculty", "staff", "directory", "leadership", "administration", 
    "about", "contact", "business", "finance", "board"
]

def is_generic_email(email: str) -> bool:
    if not email or "@" not in email: return True
    local = email.split("@", 1)[0].strip().lower()
    if GENERIC_LOCALPART_RE.search(local): return True
    if len(local) <= 3: return True
    return False

def allow_high_value_role_mailbox(email: str, context_text: str) -> bool:
    if not email or "@" not in email: return False
    local = email.split("@", 1)[0].strip().lower()
    if local not in HIGH_VALUE_ROLE_LOCALPARTS: return False
    return role_score(context_text or "") >= 80

def is_personal_email(email: str) -> bool:
    if not email or "@" not in email: return False
    local = email.split("@", 1)[0].strip().lower()
    if is_generic_email(email): return False
    return bool(PERSONALISH_RE.match(local))

NAME_RE = re.compile(r"\b(Dr\.|Mr\.|Mrs\.|Ms\.)\s+([A-Z][a-zA-Z'’-]+(?:\s+[A-Z][a-zA-Z'’-]+){1,3})\b")

def extract_name_from_text(text: str) -> str:
    if not text: return ""
    m = NAME_RE.search(text)
    if m: return (m.group(1) + " " + m.group(2)).strip()
    m2 = re.search(r"\b([A-Z][a-zA-Z'’-]+(?:\s+[A-Z][a-zA-Z'’-]+){1,3})\b", text)
    return (m2.group(1).strip() if m2 else "")

# 🔥 FUNCIÓN VANGUARD: Bautismo automático (Reemplaza los nombres vacíos por algo útil)
def generate_name_from_email(email: str) -> str:
    if not email or "@" not in email:
        return "Administrator"
    
    local = email.split("@")[0].lower().strip()
    roles_directivos = ['director', 'principal', 'head', 'headmaster', 'superintendent', 'president', 'pastor']
    roles_admin = ['info', 'admin', 'office', 'contact', 'hello', 'support', 'admissions', 'careers', 'finance']
    
    if local in roles_directivos: return "Director"
    if local in roles_admin: return "Administrator"
    
    if '.' in local: return " ".join([p.capitalize() for p in local.split('.')])
    if '_' in local: return " ".join([p.capitalize() for p in local.split('_')])
    
    return local.capitalize()

def role_score(text: str) -> int:
    if not text: return 0
    for rx, score in ROLE_PATTERNS:
        if rx.search(text): return score
    return 0

def norm_url(u: Optional[str]) -> Optional[str]:
    if not isinstance(u, str) or not u.strip(): return None
    u = u.strip()
    if not re.match(r"^https?://", u, re.I): u = "https://" + u
    return u

def same_domain(a: str, b: str) -> bool:
    try: return urlparse(a).netloc.lower().lstrip("www.") == urlparse(b).netloc.lower().lstrip("www.")
    except Exception: return False

def is_blocked_host(url: str) -> bool:
    try: return urlparse(url).netloc.lower() in BLOCKED_HOSTS
    except Exception: return False

@dataclass(frozen=True)
class Candidate:
    email: str
    name: str
    title: str
    score: int
    source_url: str

class SiteCrawler:
    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        })
        self.cache: dict[str, str] = {}

    def fetch_html(self, url: str, timeout: int = 6) -> str:
        if url in self.cache: return self.cache[url]
        try:
            r = self.session.get(url, timeout=timeout, allow_redirects=True)
            ct = r.headers.get("content-type", "")
            if r.status_code >= 400: return ""
            if "text" in ct or "html" in ct or "xml" in ct or ct == "":
                self.cache[url] = r.text
                return r.text
        except Exception: pass
        return ""

    def extract_candidates_from_page(self, html: str, url: str) -> list[Candidate]:
        if not html: return []
        soup = BeautifulSoup(html, "lxml")
        candidates: list[Candidate] = []
        full_text = soup.get_text(" ", strip=True)
        
        for m in EMAIL_RE.finditer(full_text):
            email = m.group(0)
            start = max(0, m.start() - 150)
            end = min(len(full_text), m.end() + 150)
            ctx = full_text[start:end]
            
            sc = role_score(ctx)
            if sc >= 65 and (is_personal_email(email) or allow_high_value_role_mailbox(email, ctx)):
                clean_title = (ctx[:100] + '...') if len(ctx) > 100 else ctx
                name = extract_name_from_text(ctx)
                
                # 🔥 APLICACIÓN DEL BAUTISMO
                if not name or name.strip() == "":
                    name = generate_name_from_email(email)
                    
                candidates.append(Candidate(email=email, name=name, title=clean_title, score=sc, source_url=url))

        for el in soup.find_all(string=lambda s: isinstance(s, str) and "@" in s):
            text = " ".join(str(el).split())
            ems = EMAIL_RE.findall(text)
            if not ems: continue
            parent = el.parent
            block = parent.get_text(" ", strip=True) if parent else text
            if parent and len(block) < 40 and parent.parent:
                block = parent.parent.get_text(" ", strip=True)
            for email in ems:
                ctx = block
                sc = role_score(ctx)
                if sc >= 65 and (is_personal_email(email) or allow_high_value_role_mailbox(email, ctx)):
                    name = extract_name_from_text(ctx)
                    clean_title = (ctx[:140] + "...") if len(ctx) > 140 else ctx
                    
                    # 🔥 APLICACIÓN DEL BAUTISMO
                    if not name or name.strip() == "":
                        name = generate_name_from_email(email)
                        
                    candidates.append(Candidate(email=email, name=name, title=clean_title, score=sc, source_url=url))

        best: dict[str, Candidate] = {}
        for c in candidates:
            k = c.email.lower()
            if k not in best or c.score > best[k].score: best[k] = c
        return sorted(best.values(), key=lambda x: x.score, reverse=True)

    def candidate_links(self, home_url: str, html: str) -> list[str]:
        if not html: return []
        soup = BeautifulSoup(html, "lxml")
        links: set[str] = set()
        for a in soup.select("a[href]"):
            href = (a.get("href") or "").strip()
            if not href or href.startswith("mailto:"): continue
            absu = urljoin(home_url, href)
            if not absu.startswith("http"): continue
            if not same_domain(home_url, absu): continue
            absu = absu.split("#", 1)[0]
            txt = (a.get_text(" ", strip=True) or "").lower()
            hl = absu.lower()
            if any(h in hl for h in PRIORITY_URL_HINTS) or any(h in txt for h in PRIORITY_URL_HINTS): links.add(absu)

        base = home_url.rstrip("/")
        for p in ["/faculty/", "/staff/", "/staff-directory/", "/directory/", "/leadership/", "/administration/", "/about/", "/contact/", "/business-office/", "/finance/"]:
            links.add(base + p)

        def link_priority(u: str) -> tuple[int, int, int]:
            ul = u.lower()
            score = sum(20 - idx for idx, h in enumerate(PRIORITY_URL_HINTS) if h in ul)
            try: depth = urlparse(u).path.strip("/").count("/")
            except: depth = 0
            is_profile = 1 if ("/faculty/" in ul and not ul.rstrip("/").endswith("/faculty")) or ("/staff/" in ul and not ul.rstrip("/").endswith("/staff")) else 0
            return (-is_profile, -score, -depth)

        return sorted(links, key=link_priority)

    def find_best_decision_maker(self, website: str, max_pages: int = 10) -> Optional[Candidate]:
        home = self.fetch_html(website)
        if not home: return None

        visited: set[str] = set()
        queue: list[str] = [website] + self.candidate_links(website, home)
        best: Optional[Candidate] = None
        started = time.time()

        while queue and len(visited) < max_pages:
            if time.time() - started > 6: break
            url = queue.pop(0)
            if url in visited: continue
            visited.add(url)

            html = self.fetch_html(url)
            cands = self.extract_candidates_from_page(html, url)
            if cands:
                top = cands[0]
                if top.score >= 80: return top
                if best is None or top.score > best.score: best = top

            ul = url.lower()
            if html and any(k in ul for k in ["faculty", "staff", "directory", "leadership", "administration"]):
                nxts = [nxt for nxt in self.candidate_links(website, html)[:18] if nxt not in visited and nxt not in queue]
                if nxts: queue[0:0] = nxts

        if best and best.score >= 65: return best
        return None

def main() -> int:
    if len(sys.argv) < 3:
        print("Usage: enrich_decision_makers.py INPUT_XLSX OUTPUT_XLSX", file=sys.stderr)
        return 2

    in_path = sys.argv[1]
    out_path = sys.argv[2]
    df = pd.read_excel(in_path, sheet_name=SHEET)

    for col in ["Decision Maker Name", "Title", "Email", "Email Source URL", "Email Confidence"]:
        if col not in df.columns: df[col] = pd.NA

    crawler = SiteCrawler()
    missing = df["Email"].isna() | (df["Email"].astype(str).str.strip() == "")
    idxs = df.index[missing].tolist()
    print(f"🔥 INICIANDO RADAR VANGUARD V3 (Auto-Naming). Objetivos: {len(idxs)}")

    filled = 0
    for n, i in enumerate(idxs, 1):
        website = norm_url(df.at[i, "Website"] if "Website" in df.columns else None)
        if not website: continue
        if is_blocked_host(website): continue

        school = str(df.at[i, "School Name"])
        print(f"[{n}/{len(idxs)}] Explorando: {school}", flush=True)
        cand = crawler.find_best_decision_maker(website, max_pages=10)
        
        if cand:
            df.at[i, "Email"] = cand.email
            if cand.name: df.at[i, "Decision Maker Name"] = cand.name
            if cand.title: df.at[i, "Title"] = cand.title
            df.at[i, "Email Source URL"] = cand.source_url
            df.at[i, "Email Confidence"] = "strict_personal_website"
            filled += 1
            print(f"   🎯 IMPACTO: {cand.email} | Nombre asigado: {cand.name}")

        if n % 10 == 0:
            with pd.ExcelWriter(out_path, engine="openpyxl") as w:
                df.to_excel(w, index=False, sheet_name=SHEET)

    print(f"\n✅ OPERACIÓN COMPLETADA. Nuevos leads inyectados: {filled}")
    with pd.ExcelWriter(out_path, engine="openpyxl") as w:
        df.to_excel(w, index=False, sheet_name=SHEET)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())