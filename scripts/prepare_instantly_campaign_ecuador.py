#!/usr/bin/env python3
"""
Prepara CSV de leads (p. ej. export Apify) para una campaña en Instantly:
- Quita correos genéricos (local part en lista de baneo).
- Puntúa y ordena (.ec / roles / Instagram).
- Dedup por email.
- Opcional: CSV mínimo con columnas típicas de Instantly (email + custom fields).

Uso:
  python scripts/prepare_instantly_campaign_ecuador.py apify_results.csv -o leads_ecuador_ready.csv
  python scripts/prepare_instantly_campaign_ecuador.py apify_results.csv -o instantly.csv --instantly-minimal
  python scripts/prepare_instantly_campaign_ecuador.py places.csv -o prep.csv --google-places
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

GENERIC_PREFIXES = frozenset(
    {
        "info",
        "ventas",
        "contact",
        "contacto",
        "admin",
        "soporte",
        "support",
        "sales",
        "reception",
        "recepcion",
        "customerservice",
        "hello",
        "hola",
        "marketing",
        "queries",
        "general",
    }
)

ROLE_SUBSTRINGS = (
    "gerencia",
    "director",
    "ceo",
    "owner",
    "dueno",
    "manager",
)

# Columnas que Instantly suele mapear bien como variables (si existen en el origen)
INSTANTLY_OPTIONAL_COLUMNS = (
    "first_name",
    "last_name",
    "firstName",
    "lastName",
    "company",
    "company_name",
    "title",
    "website",
    "domain",
    "instagram_url",
    "linkedin_url",
    "phone",
    "city",
    "country",
)


def _resolve_email_column(df: pd.DataFrame) -> str:
    for col in ("email", "Email", "EMAIL", "e_mail", "E-mail"):
        if col in df.columns:
            return col
    raise ValueError(
        "No se encontró columna de email. Esperada una de: email, Email, EMAIL."
    )


def _normalize_email(value: object) -> str | None:
    if pd.isna(value):
        return None
    s = str(value).strip()
    if not s or "@" not in s:
        return None
    return s


def is_generic_email(email: str | None) -> bool:
    if not email:
        return True
    local = email.split("@", 1)[0].lower().strip()
    return local in GENERIC_PREFIXES


def calculate_score(row: pd.Series, email_col: str) -> int:
    score = 0
    email = str(row.get(email_col, "") or "").lower()

    if email.endswith(".ec") or email.endswith(".com.ec"):
        score += 50

    if any(role in email for role in ROLE_SUBSTRINGS):
        score += 30

    ig = row.get("instagram_url")
    if pd.notna(ig) and str(ig).strip():
        score += 20

    return score


def clean_and_prioritize_leads(
    df: pd.DataFrame,
    email_col: str | None = None,
) -> pd.DataFrame:
    col = email_col or _resolve_email_column(df)
    work = df.copy()
    work["_email_norm"] = work[col].map(_normalize_email)
    work = work[work["_email_norm"].notna()].copy()
    work[col] = work["_email_norm"]
    work = work.drop(columns=["_email_norm"])

    mask = ~work[col].map(is_generic_email)
    df_clean = work.loc[mask].copy()

    df_clean["lead_score"] = df_clean.apply(
        lambda r: calculate_score(r, col), axis=1
    )
    df_clean = df_clean.sort_values(by="lead_score", ascending=False)
    df_clean = df_clean.drop_duplicates(subset=[col], keep="first")
    return df_clean


def _is_google_places_export(df: pd.DataFrame) -> bool:
    """Dataset típico Apify actor crawler-google-places (sin columna email)."""
    need = {"title", "url", "website"}
    if not need.issubset(set(df.columns)):
        return False
    email_hints = ("email", "Email", "EMAIL")
    return not any(c in df.columns for c in email_hints)


def score_google_places_row(row: pd.Series) -> int:
    """Prioriza EC, web con Instagram, filas con web y teléfono."""
    score = 0
    if str(row.get("countryCode", "") or "").strip().upper() == "EC":
        score += 50
    ws = str(row.get("website", "") or "").lower()
    if ws and ws not in ("nan", "none"):
        score += 15
    if "instagram.com" in ws:
        score += 20
    ph = row.get("phone")
    if pd.notna(ph) and str(ph).strip():
        score += 10
    return score


def clean_and_prioritize_google_places(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normaliza export Places: score, dedup por URL de Maps, columnas útiles para enriquecer emails.
    No genera email: Instantly requiere enriquecimiento previo (Hunter, manual, otro actor).
    """
    work = df.copy()
    work["lead_score"] = work.apply(score_google_places_row, axis=1)
    maps_col = "url"
    work = work.dropna(subset=[maps_col], how="all")
    work[maps_col] = work[maps_col].astype(str).str.strip()
    work = work[work[maps_col].str.len() > 0]
    work = work.sort_values(by="lead_score", ascending=False)
    work = work.drop_duplicates(subset=[maps_col], keep="first")

    # Columnas estables para merge posterior con un CSV que sí tenga email
    rename_map = {
        "title": "company_name",
        "url": "google_maps_url",
        "countryCode": "country",
    }
    out = work.rename(columns={k: v for k, v in rename_map.items() if k in work.columns})
    if "email" not in out.columns:
        out.insert(0, "email", "")
    return out


def to_instantly_minimal(df: pd.DataFrame, email_col: str) -> pd.DataFrame:
    """Solo columnas seguras para import; email en minúsculas estándar."""
    out_cols: list[str] = [email_col]
    for c in INSTANTLY_OPTIONAL_COLUMNS:
        if c in df.columns and c not in out_cols:
            out_cols.append(c)
    if "lead_score" in df.columns:
        out_cols.append("lead_score")
    mini = df[out_cols].copy()
    mini = mini.rename(columns={email_col: "email"})
    return mini


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Limpia y prioriza leads para campaña Instantly (Ecuador / Apify)."
    )
    parser.add_argument(
        "input_csv",
        type=Path,
        help="CSV exportado (Apify u otro).",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        required=True,
        help="Ruta del CSV de salida.",
    )
    parser.add_argument(
        "--email-column",
        default=None,
        help="Nombre de la columna de email si no es 'email' / 'Email'.",
    )
    parser.add_argument(
        "--instantly-minimal",
        action="store_true",
        help="Escribir solo email + columnas opcionales conocidas + lead_score.",
    )
    parser.add_argument(
        "--google-places",
        action="store_true",
        help="CSV Apify Google Places (sin emails): score + dedup Maps + columna email vacía para pipeline.",
    )
    args = parser.parse_args()

    if not args.input_csv.is_file():
        print(f"Error: no existe el archivo {args.input_csv}", file=sys.stderr)
        return 1

    df = pd.read_csv(args.input_csv)

    if args.email_column and args.email_column not in df.columns:
        print(
            f"Error: la columna --email-column '{args.email_column}' no existe en el CSV.",
            file=sys.stderr,
        )
        return 1

    use_places = bool(args.google_places)
    email_col_resolved: str | None = args.email_column
    if not use_places:
        try:
            email_col_resolved = email_col_resolved or _resolve_email_column(df)
        except ValueError:
            if _is_google_places_export(df):
                use_places = True
                print(
                    "Info: CSV sin email, columnas tipo Google Places — "
                    "usando modo Places (score + dedup Maps).",
                    file=sys.stderr,
                )
            else:
                print(
                    "Error: no hay columna de email y el CSV no parece export "
                    "Google Places (title, url, website).",
                    file=sys.stderr,
                )
                return 1

    if use_places and args.instantly_minimal:
        print(
            "Error: --google-places y --instantly-minimal no son compatibles (no hay emails).",
            file=sys.stderr,
        )
        return 1

    if use_places:
        if args.google_places and not _is_google_places_export(df):
            print(
                "Advertencia: el CSV no coincide con el patrón Places esperado "
                "(title, url, website). Se procesa igual como Places.",
                file=sys.stderr,
            )
        df_clean = clean_and_prioritize_google_places(df)
        out = df_clean
        extra = (
            " Modo Places: sin emails en origen — enriquece antes de subir a Instantly."
        )
    else:
        assert email_col_resolved is not None
        df_clean = clean_and_prioritize_leads(df, email_col=email_col_resolved)
        if args.instantly_minimal:
            out = to_instantly_minimal(df_clean, email_col_resolved)
        else:
            out = df_clean
        extra = ""

    args.output.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.output, index=False)
    print(
        f"Listo. Originales: {len(df)} | "
        f"Filas salida: {len(out)} | "
        f"Salida: {args.output}.{extra}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
