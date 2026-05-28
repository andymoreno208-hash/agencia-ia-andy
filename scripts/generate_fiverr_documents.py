from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List


def _try_import_reportlab():
    try:
        from reportlab.lib import colors  # noqa: F401
        from reportlab.lib.pagesizes import letter  # noqa: F401
        from reportlab.lib.styles import getSampleStyleSheet  # noqa: F401
        from reportlab.platypus import SimpleDocTemplate  # noqa: F401
    except Exception as e:  # pragma: no cover
        raise SystemExit(
            "reportlab is not installed. Run:\n"
            "  python3 -m venv .venv\n"
            "  .venv/bin/pip install reportlab\n"
            "Then rerun:\n"
            "  .venv/bin/python scripts/generate_fiverr_documents.py"
        ) from e


@dataclass(frozen=True)
class LeadRow:
    company: str
    website: str
    decision_maker: str
    title: str
    email: str
    phone: str
    city: str
    state: str
    source_url: str


def demo_rows() -> List[LeadRow]:
    # 100% demo/fake data (do not use real client data in public portfolio)
    return [
        LeadRow(
            company="Northstar Accounting Group",
            website="https://northstaraccounting.example",
            decision_maker="Jordan Reed",
            title="Managing Partner",
            email="jordan.reed@northstaraccounting.example",
            phone="(469) 555-0142",
            city="Dallas",
            state="TX",
            source_url="https://northstaraccounting.example/team",
        ),
        LeadRow(
            company="Evergreen Dental Partners",
            website="https://evergreendentaltx.example",
            decision_maker="Sofia Martinez",
            title="Office Manager",
            email="sofia.martinez@evergreendentaltx.example",
            phone="(972) 555-0175",
            city="Plano",
            state="TX",
            source_url="https://evergreendentaltx.example/about",
        ),
        LeadRow(
            company="Cedar Ridge MedSpa",
            website="https://cedarridgemedspa.example",
            decision_maker="Avery Collins",
            title="Practice Manager",
            email="avery.collins@cedarridgemedspa.example",
            phone="(214) 555-0199",
            city="Fort Worth",
            state="TX",
            source_url="https://cedarridgemedspa.example/team",
        ),
        LeadRow(
            company="Summit Law Offices",
            website="https://summitlawtx.example",
            decision_maker="Mason Price",
            title="Partner",
            email="mason.price@summitlawtx.example",
            phone="(817) 555-0106",
            city="Arlington",
            state="TX",
            source_url="https://summitlawtx.example/attorneys",
        ),
        LeadRow(
            company="Collin County Private School",
            website="https://collinprivateschool.example",
            decision_maker="Emma Nguyen",
            title="Director of Finance",
            email="emma.nguyen@collinprivateschool.example",
            phone="(469) 555-0118",
            city="Frisco",
            state="TX",
            source_url="https://collinprivateschool.example/staff",
        ),
        LeadRow(
            company="Rockwall Community Church",
            website="https://rockwallcommunitychurch.example",
            decision_maker="Noah Turner",
            title="Business Administrator",
            email="noah.turner@rockwallcommunitychurch.example",
            phone="(214) 555-0133",
            city="Rockwall",
            state="TX",
            source_url="https://rockwallcommunitychurch.example/contact",
        ),
        LeadRow(
            company="Tarrant Medical Associates",
            website="https://tarrantmedical.example",
            decision_maker="Olivia Brooks",
            title="Operations Director",
            email="olivia.brooks@tarrantmedical.example",
            phone="(817) 555-0164",
            city="Fort Worth",
            state="TX",
            source_url="https://tarrantmedical.example/leadership",
        ),
        LeadRow(
            company="Denton Family Dentistry",
            website="https://dentonfamilydentistry.example",
            decision_maker="Ethan Patel",
            title="Practice Owner",
            email="ethan.patel@dentonfamilydentistry.example",
            phone="(940) 555-0180",
            city="Denton",
            state="TX",
            source_url="https://dentonfamilydentistry.example/about",
        ),
        LeadRow(
            company="Dallas Wellness Clinic",
            website="https://dallaswellnessclinic.example",
            decision_maker="Mia Johnson",
            title="Clinic Administrator",
            email="mia.johnson@dallaswellnessclinic.example",
            phone="(214) 555-0157",
            city="Dallas",
            state="TX",
            source_url="https://dallaswellnessclinic.example/team",
        ),
        LeadRow(
            company="Bluebonnet CPA Firm",
            website="https://bluebonnetcpa.example",
            decision_maker="Lucas Bennett",
            title="Managing Partner",
            email="lucas.bennett@bluebonnetcpa.example",
            phone="(972) 555-0129",
            city="McKinney",
            state="TX",
            source_url="https://bluebonnetcpa.example/partners",
        ),
    ]


def build_sample_pdf(out_path: Path) -> None:
    _try_import_reportlab()
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(str(out_path), pagesize=letter, title="10-Lead Sample (Demo)")

    story = []
    story.append(Paragraph("10-Lead Sample (Demo) — Verified Decision Makers", styles["Title"]))
    story.append(Paragraph("Demo data for format preview. Final delivery uses your exact niche/location/titles.", styles["Normal"]))
    story.append(Spacer(1, 12))

    rows = demo_rows()
    header = ["Company", "Website", "Decision Maker", "Title", "Email", "Phone", "City", "State", "Source URL"]
    data = [header] + [
        [
            r.company,
            r.website,
            r.decision_maker,
            r.title,
            r.email,
            r.phone,
            r.city,
            r.state,
            r.source_url,
        ]
        for r in rows
    ]

    table = Table(
        data,
        colWidths=[110, 95, 85, 75, 125, 70, 60, 35, 140],
        repeatRows=1,
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0B2B3A")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 8),
                ("FONTSIZE", (0, 1), (-1, -1), 7),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 12))
    story.append(Paragraph("Note: No generic inboxes (info@/admin@/admissions@). Sources included for audit.", styles["Italic"]))

    doc.build(story)


def build_upwork_delivery_standard_pdf(out_path: Path) -> None:
    _try_import_reportlab()
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import ListFlowable, ListItem, Paragraph, SimpleDocTemplate, Spacer

    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(
        str(out_path),
        pagesize=letter,
        title="Vanguard B2B List — Delivery Standard",
    )

    story = []
    story.append(Paragraph("Vanguard B2B List — Delivery Standard", styles["Title"]))
    story.append(
        Paragraph(
            "Fictional / illustrative only — not a real client export.",
            styles["Italic"],
        )
    )
    story.append(Spacer(1, 12))

    story.append(Paragraph("What's included (typical columns)", styles["Heading2"]))
    included = [
        "Company name + website",
        "Decision-maker name + title (when publicly available)",
        "Best-available email + phone",
        "City / state / country (as scoped)",
        "Source URL or sourcing note (audit-friendly)",
    ]
    story.append(
        ListFlowable(
            [ListItem(Paragraph(x, styles["Normal"])) for x in included],
            bulletType="bullet",
            leftIndent=18,
        )
    )
    story.append(Spacer(1, 10))

    story.append(Paragraph("QA pass (every delivery)", styles["Heading2"]))
    qa = [
        "ICP + geography matched to your brief",
        "Dedupe within batch",
        "Remove obvious placeholders / generic junk where applicable",
        "Consistent column headers for import",
        "Google Sheet + CSV export",
    ]
    story.append(
        ListFlowable([ListItem(Paragraph(x, styles["Normal"])) for x in qa], bulletType="bullet", leftIndent=18)
    )
    story.append(Spacer(1, 10))

    story.append(Paragraph("What I don't guarantee", styles["Heading2"]))
    limits = [
        "Personal email on every row (varies by industry/site)",
        "Zero bounce / 100% verified (catch-all domains exist)",
        "Outreach or sending on your behalf",
    ]
    story.append(
        ListFlowable([ListItem(Paragraph(x, styles["Normal"])) for x in limits], bulletType="bullet", leftIndent=18)
    )
    story.append(Spacer(1, 10))

    story.append(Paragraph("Recommended start", styles["Heading2"]))
    story.append(
        Paragraph(
            "15-row paid pilot (Starter tier) → you approve → scale to 50/100 rows.",
            styles["Normal"],
        )
    )
    story.append(Spacer(1, 10))

    story.append(Paragraph("Delivery timeline", styles["Heading2"]))
    story.append(
        Paragraph(
            "Per tier after requirements received: Starter 2 days · Standard 5 days · Advanced 7 days.",
            styles["Normal"],
        )
    )

    doc.build(story)


def build_qc_pdf(out_path: Path) -> None:
    """Legacy Fiverr QC doc — delegates to Upwork-safe standard."""
    build_upwork_delivery_standard_pdf(out_path)


def build_cleanup_before_after_pdf(out_path: Path) -> None:
    _try_import_reportlab()
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(str(out_path), pagesize=letter, title="CSV Cleanup — Before/After (Demo)")

    before_header = ["name", "email??", "phone", "city/state", "company"]
    before_rows = [
        ["  john  SMITH", "INFO@ACME.com ", "214.555.0199", "dallas, texas", "Acme  LLC"],
        ["John Smith", "info@acme.com", "214-555-0199", "Dallas TX", "ACME LLC"],
        ["mary-jane lopez", " mary.lopez@northstar.example", " (972)5550175 ", "plano / tx", "NorthStar  Accounting"],
        ["Mary Jane Lopez", "MARY.LOPEZ@NORTHSTAR.EXAMPLE", "9725550175", "Plano,TX", "Northstar Accounting"],
        ["", "admin@evergreen.example", "", "Fort Worth, TX", "Evergreen Dental"],
    ]

    after_header = ["Name", "Email", "Phone", "City", "State", "Company"]
    after_rows = [
        ["John Smith", "info@acme.com", "(214) 555-0199", "Dallas", "TX", "Acme LLC"],
        ["Mary Jane Lopez", "mary.lopez@northstar.example", "(972) 555-0175", "Plano", "TX", "Northstar Accounting"],
        ["(removed)", "(removed)", "(removed)", "(removed)", "(removed)", "(removed)  # blank row / invalid"],
    ]

    story = []
    story.append(Paragraph("CSV Cleanup — Before/After (Demo)", styles["Title"]))
    story.append(
        Paragraph(
            "Demo data showing typical issues: duplicates, inconsistent casing, broken formatting, and blank rows.",
            styles["Normal"],
        )
    )
    story.append(Spacer(1, 12))

    story.append(Paragraph("BEFORE (raw / messy)", styles["Heading2"]))
    before_table = Table([before_header] + before_rows, colWidths=[105, 160, 95, 95, 120], repeatRows=1)
    before_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2B2B2B")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 8),
                ("FONTSIZE", (0, 1), (-1, -1), 7),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
            ]
        )
    )
    story.append(before_table)
    story.append(Spacer(1, 14))

    story.append(Paragraph("AFTER (clean / standardized)", styles["Heading2"]))
    after_table = Table([after_header] + after_rows, colWidths=[105, 160, 95, 85, 40, 140], repeatRows=1)
    after_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0B2B3A")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 8),
                ("FONTSIZE", (0, 1), (-1, -1), 7),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
            ]
        )
    )
    story.append(after_table)
    story.append(Spacer(1, 10))
    story.append(
        Paragraph(
            "Summary (demo): duplicates merged, casing normalized, phone formatted, city/state split, blank rows removed.",
            styles["Italic"],
        )
    )

    doc.build(story)


def build_cleanup_scope_checklist_pdf(out_path: Path) -> None:
    _try_import_reportlab()
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import ListFlowable, ListItem, Paragraph, SimpleDocTemplate, Spacer

    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(str(out_path), pagesize=letter, title="CSV Cleanup — Scope + Checklist")

    story = []
    story.append(Paragraph("CSV Cleanup — Scope + Checklist", styles["Title"]))
    story.append(Paragraph("Portfolio-friendly overview (no client data).", styles["Normal"]))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Included (cleanup):", styles["Heading2"]))
    included = [
        "Remove duplicates (exact + near-duplicates when possible)",
        "Standardize columns (e.g., Name, Title, Email, Phone, Company, City, State, Website)",
        "Fix formatting issues (extra spaces, mixed casing, broken rows)",
        "Normalize phone numbers (when possible)",
        "Deliver an import-ready CSV + short summary",
    ]
    story.append(
        ListFlowable([ListItem(Paragraph(x, styles["Normal"])) for x in included], bulletType="bullet", leftIndent=18)
    )
    story.append(Spacer(1, 10))

    story.append(Paragraph("Not included (unless custom add-on):", styles["Heading2"]))
    not_included = [
        "Creating brand-new leads from scratch",
        "Filling missing emails/phones/websites for every row",
        "Verification of deliverability (separate service)",
    ]
    story.append(
        ListFlowable([ListItem(Paragraph(x, styles["Normal"])) for x in not_included], bulletType="bullet", leftIndent=18)
    )
    story.append(Spacer(1, 12))

    story.append(Paragraph("What I need from you:", styles["Heading2"]))
    need = [
        "Upload CSV/XLSX",
        "Desired final columns/order (or a sample row)",
        "Any rules (remove generic emails like info@/admin@, country/state format, etc.)",
    ]
    story.append(ListFlowable([ListItem(Paragraph(x, styles["Normal"])) for x in need], bulletType="bullet", leftIndent=18))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Typical delivery: 24–48h (depends on rows + complexity).", styles["Heading3"]))
    doc.build(story)


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    out_dir = root / "fiverr_docs"
    out_dir.mkdir(parents=True, exist_ok=True)

    sample_pdf = out_dir / "10-lead-sample-demo.pdf"
    qc_pdf = out_dir / "quality-checklist-deliverable-fields.pdf"
    upwork_pdf = root / "campaign_outputs" / "upwork-vanguard-delivery-standard.pdf"
    cleanup_before_after_pdf = out_dir / "csv-cleanup-before-after-demo.pdf"
    cleanup_scope_pdf = out_dir / "csv-cleanup-scope-checklist.pdf"

    build_sample_pdf(sample_pdf)
    build_upwork_delivery_standard_pdf(upwork_pdf)
    build_qc_pdf(qc_pdf)
    build_cleanup_before_after_pdf(cleanup_before_after_pdf)
    build_cleanup_scope_checklist_pdf(cleanup_scope_pdf)

    print(
        "Created:\n"
        f"- {sample_pdf}\n"
        f"- {upwork_pdf}\n"
        f"- {qc_pdf}\n"
        f"- {cleanup_before_after_pdf}\n"
        f"- {cleanup_scope_pdf}"
    )


if __name__ == "__main__":
    main()

