"""PDF generation service — builds professional client qualification reports."""
from __future__ import annotations

import io
from datetime import datetime
from typing import Any, Dict, List

from app.modules.reports.services.explanation_service import (
    enrich_all_products,
    enrich_criteria_explanations,
)

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    HRFlowable,
    KeepTogether,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.flowables import Flowable

# ── Brand colours ─────────────────────────────────────────────────────────────
NAVY   = colors.HexColor("#1B2A4A")
ORANGE = colors.HexColor("#E8622C")
LIGHT  = colors.HexColor("#F5F7FA")
MID    = colors.HexColor("#E2E8F0")
GREEN  = colors.HexColor("#22C55E")
AMBER  = colors.HexColor("#F59E0B")
RED    = colors.HexColor("#EF4444")
GREY   = colors.HexColor("#64748B")
WHITE  = colors.white
INDIGO = colors.HexColor("#EEF2FF")

W, H   = A4
MARGIN = 18 * mm


# ── Custom flowables ───────────────────────────────────────────────────────────
class LeytonHeader(Flowable):
    HEIGHT = 24 * mm

    def __init__(self, content_width: float, margin: float):
        super().__init__()
        self.content_width = content_width
        self.margin        = margin
        # reportlab uses self.width for layout — occupy only the frame width
        self.width  = content_width
        self.height = self.HEIGHT

    def draw(self):
        c        = self.canv
        full_w   = self.content_width + 2 * self.margin
        m        = self.margin
        baseline = self.HEIGHT / 2 - 5

        # Shift left to the true page edge so the banner is full-width
        c.saveState()
        c.translate(-m, 0)

        # Navy background spanning full page width
        c.setFillColor(NAVY)
        c.rect(0, 0, full_w, self.HEIGHT, fill=1, stroke=0)

        # LEYT (white) · O (orange) · N (white)
        c.setFont("Helvetica-Bold", 20)
        c.setFillColor(WHITE);  c.drawString(m, baseline, "LEYT")
        c.setFillColor(ORANGE); c.drawString(m + 54, baseline, "O")
        c.setFillColor(WHITE);  c.drawString(m + 67, baseline, "N")

        # Tagline
        c.setFont("Helvetica", 7)
        c.setFillColor(colors.HexColor("#94A3B8"))
        c.drawString(m, baseline - 11, "Empower your future")

        # Sellynx badge — right-aligned with margin
        badge_w = 52
        bx = full_w - m - badge_w
        by = self.HEIGHT / 2 - 8
        c.setFillColor(ORANGE)
        c.roundRect(bx, by, badge_w, 15, 3, fill=1, stroke=0)
        c.setFillColor(WHITE)
        c.setFont("Helvetica-Bold", 7)
        c.drawCentredString(bx + badge_w / 2, by + 4, "SELLYNX AI")

        c.restoreState()


# ── Styles ─────────────────────────────────────────────────────────────────────
def _s() -> Dict[str, ParagraphStyle]:
    return {
        "h1":    ParagraphStyle("H1",    fontName="Helvetica-Bold", fontSize=18, textColor=NAVY,   spaceAfter=10),
        "h2":    ParagraphStyle("H2",    fontName="Helvetica-Bold", fontSize=12, textColor=NAVY,   spaceBefore=10, spaceAfter=4),
        "h3":    ParagraphStyle("H3",    fontName="Helvetica-Bold", fontSize=10, textColor=NAVY,   spaceBefore=4, spaceAfter=2),
        "body":  ParagraphStyle("Body",  fontName="Helvetica",      fontSize=9,  textColor=colors.HexColor("#334155"), leading=14),
        "small": ParagraphStyle("Small", fontName="Helvetica",      fontSize=8,  textColor=GREY,   leading=12),
        "label": ParagraphStyle("Label", fontName="Helvetica-Bold", fontSize=8,  textColor=GREY,   spaceAfter=1),
        "quote": ParagraphStyle("Quote", fontName="Helvetica-Oblique", fontSize=8, textColor=GREY, leftIndent=8, leading=12),
        "kpi_v": ParagraphStyle("KpiV",  fontName="Helvetica-Bold", fontSize=20, textColor=NAVY,   alignment=1, leading=24),
        "kpi_l": ParagraphStyle("KpiL",  fontName="Helvetica",      fontSize=8,  textColor=GREY,   alignment=1, leading=11),
        "expl":  ParagraphStyle("Expl",  fontName="Helvetica",      fontSize=8,  textColor=colors.HexColor("#1E3A5F"), leading=13, leftIndent=4),
        "why":   ParagraphStyle("Why",   fontName="Helvetica",      fontSize=9,  textColor=colors.HexColor("#7F1D1D"),
                                backColor=colors.HexColor("#FEF2F2"), borderPad=6, leading=14, leftIndent=6),
    }


# ── Colour helpers ─────────────────────────────────────────────────────────────
def _elig_color(status: str) -> Any:
    return {"eligible": GREEN, "to_review": AMBER}.get(status, RED)

def _elig_label(status: str) -> str:
    return {"eligible": "✓ Eligible", "to_review": "~ To Review"}.get(status, "✗ Not Eligible")

def _score_color(pct: float) -> Any:
    return GREEN if pct >= 75 else (AMBER if pct >= 40 else RED)

def _hex(c: Any) -> str:
    return f"{int(c.red*255):02X}{int(c.green*255):02X}{int(c.blue*255):02X}"

def _pct(r: Dict[str, Any]) -> int:
    s = r.get("summary", {})
    return round((s.get("total_score", 0) / max(s.get("max_score", 1), 1)) * 100)


# ── KPI tile (nested table — fixes overlap bug) ────────────────────────────────
def _kpi_cell(label: str, value: str) -> Table:
    st = _s()
    t = Table(
        [[Paragraph(value, st["kpi_v"])],
         [Paragraph(label, st["kpi_l"])]],
        colWidths=[None],
        rowHeights=[26, 14],
    )
    t.setStyle(TableStyle([
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
    ]))
    return t


# ── Single criterion card (with explanation) ───────────────────────────────────
def _criterion_card(c: Dict, st: Dict, doc_width: float) -> List[Any]:
    """Render one criterion as a readable card: label + answer + explanation + quote."""
    label      = c.get("label", "Critère")
    answer     = c.get("predicted_answer", "unknown")
    score      = c.get("score", 0)
    max_sc     = c.get("max_score", 0)
    conf       = round((c.get("confidence") or 0) * 100)
    explanation = c.get("explanation", "")
    ev          = c.get("evidence") or {}
    exact_quote = ev.get("exact_quote", "")
    source_lbl  = ev.get("source_label", "")

    ans_txt = "Non déterminé" if (not answer or answer == "unknown") else answer
    sc_col  = GREEN if score == max_sc else (AMBER if score > 0 else RED)

    items: List[Any] = []

    # ── Header row: label left · score right ──────────────────────────────────
    header = Table([[
        Paragraph(f"<b>{label}</b>", st["body"]),
        Paragraph(
            f'<font color="#{_hex(sc_col)}"><b>{score}/{max_sc} pts</b></font>'
            + (f' <font color="#94A3B8">· {conf}%</font>' if answer != "unknown" else ""),
            ParagraphStyle("CrHdr", fontName="Helvetica-Bold", fontSize=8,
                           textColor=NAVY, alignment=2),
        ),
    ]], colWidths=[doc_width * 0.68, doc_width * 0.32])
    header.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), INDIGO),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
    ]))
    items.append(header)

    # ── Body: answer + explanation ────────────────────────────────────────────
    ans_color = _hex(sc_col)
    body_data = [
        [Paragraph(
            f'<b>Réponse :</b> <font color="#{ans_color}">{ans_txt}</font>',
            st["body"],
        )],
        [Paragraph(
            f"<b>Explication :</b> {explanation}",
            st["expl"],
        )],
    ]
    body_tbl = Table(body_data, colWidths=[doc_width])
    body_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), WHITE),
        ("TOPPADDING",    (0, 0), (0, 0),   6),
        ("BOTTOMPADDING", (0, 0), (0, 0),   2),
        ("TOPPADDING",    (0, 1), (0, 1),   3),
        ("BOTTOMPADDING", (0, 1), (0, 1),   6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
        ("LINEBELOW",     (0, -1), (-1, -1), 0.4, MID),
    ]))
    items.append(body_tbl)

    # ── Optional evidence quote ───────────────────────────────────────────────
    if exact_quote:
        q_text = exact_quote[:280].strip()
        suffix = "…" if len(exact_quote) > 280 else ""
        src    = f" <font color='#94A3B8'>— {source_lbl}</font>" if source_lbl else ""
        items.append(
            Paragraph(f'<i>« {q_text}{suffix} »{src}</i>', st["quote"])
        )
        items.append(Spacer(1, 1.5 * mm))

    items.append(Spacer(1, 2 * mm))
    return items


# ── Criteria card list (replaces old compact table) ────────────────────────────
def _criteria_cards(
    criteria: List[Dict],
    st: Dict,
    doc_width: float,
    only_failed: bool = False,
    max_items: int = 6,
) -> List[Any]:
    """Return a list of criterion cards, sorted and filtered."""
    if only_failed:
        pool = sorted(
            criteria,
            key=lambda c: (c.get("predicted_answer", "unknown") == "unknown", -c.get("score", 0)),
        )
    else:
        pool = [c for c in criteria if c.get("predicted_answer", "unknown") != "unknown"]
        pool = sorted(pool, key=lambda c: c.get("score", 0), reverse=True)

    items: List[Any] = []
    for c in pool[:max_items]:
        items.extend(_criterion_card(c, st, doc_width))
    return items


# ── Product block builder ──────────────────────────────────────────────────────
def _product_block(
    pr: Dict,
    st: Dict,
    doc_width: float,
) -> List[Any]:
    s            = pr.get("summary", {})
    elig         = s.get("eligibility_status", "not_eligible")
    ec           = _elig_color(elig)
    pct          = _pct(pr)
    is_not_elig  = elig == "not_eligible"
    product_name = pr.get("product_name", pr.get("product_id", ""))

    # criteria already enriched with 'explanation' key by enrich_all_products()
    criteria = pr.get("criteria_results", [])

    block: List[Any] = []

    # ── Product header ────────────────────────────────────────────────────────
    ph = Table([[
        Paragraph(
            f"<b>{product_name}</b> "
            f"<font color='#64748B'>({pr.get('product_id', '')})</font>",
            st["h3"],
        ),
        Paragraph(
            f'<font color="#{_hex(ec)}"><b>{_elig_label(elig)}</b></font>'
            f' — <font color="#{_hex(_score_color(pct))}"><b>{pct}%</b></font>',
            st["body"],
        ),
    ]], colWidths=[doc_width * 0.55, doc_width * 0.45])
    ph.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), LIGHT),
        ("TOPPADDING",    (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
        ("LINEBELOW",     (0, 0), (-1, -1), 1.5, ec),
    ]))
    block.append(ph)
    block.append(Spacer(1, 2 * mm))

    if is_not_elig:
        # Summary sentence of what failed
        failed  = [c for c in criteria if c.get("score", 0) == 0 and c.get("predicted_answer", "unknown") != "unknown"]
        missing = [c for c in criteria if c.get("predicted_answer", "unknown") == "unknown"]
        reasons: List[str] = []
        if missing:
            names = ", ".join(c.get("label", "?") for c in missing[:3])
            reasons.append(
                f"{len(missing)} critère(s) n'ont pas pu être vérifiés : {names}"
                + ("…" if len(missing) > 3 else "") + "."
            )
        if failed:
            names = ", ".join(c.get("label", "?") for c in failed[:3])
            reasons.append(
                f"{len(failed)} critère(s) ne satisfont pas les seuils requis : {names}"
                + ("…" if len(failed) > 3 else "") + "."
            )
        if not reasons:
            reasons.append("Le score global n'atteint pas le seuil minimal d'éligibilité.")

        block.append(Paragraph(
            "<b>Pourquoi non éligible : </b>" + " ".join(reasons),
            st["why"],
        ))
        block.append(Spacer(1, 2 * mm))
        block.extend(_criteria_cards(criteria, st, doc_width, only_failed=True, max_items=5))
    else:
        block.extend(_criteria_cards(criteria, st, doc_width, only_failed=False, max_items=6))

    block.append(Spacer(1, 4 * mm))
    return block


# ── Main entry point ───────────────────────────────────────────────────────────
def build_pdf(client: Dict[str, Any], batch_result: Dict[str, Any]) -> bytes:
    """Return PDF bytes for the given client qualification result."""
    buf = io.BytesIO()
    st  = _s()

    doc = BaseDocTemplate(
        buf, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN,  bottomMargin=MARGIN,
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="main")
    doc.addPageTemplates([PageTemplate(id="main", frames=[frame])])

    story: List[Any] = []

    # ── Header ────────────────────────────────────────────────────────────────
    story.append(LeytonHeader(doc.width, MARGIN))
    story.append(Spacer(1, 6 * mm))

    # ── Title ─────────────────────────────────────────────────────────────────
    story.append(Paragraph("Client Qualification Report", st["h1"]))
    story.append(Paragraph(
        f"Generated on {datetime.today().strftime('%d %B %Y')} &nbsp;·&nbsp; Powered by Sellynx AI",
        st["small"],
    ))
    story.append(Spacer(1, 4 * mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=MID))
    story.append(Spacer(1, 4 * mm))

    # ── Client overview ────────────────────────────────────────────────────────
    story.append(Paragraph("Client Overview", st["h2"]))
    info_rows = [
        ("Company",       client.get("client_name", "—")),
        ("Salesforce ID", client.get("client_id",   "—")),
        ("Sector",        client.get("sector")       or "—"),
        ("Employees",     str(client.get("employees") or "—")),
        ("Website",       client.get("website")      or "—"),
    ]
    info_tbl = Table(
        [[Paragraph(f"<b>{k}</b>", st["label"]), Paragraph(str(v), st["body"])]
         for k, v in info_rows],
        colWidths=[40 * mm, doc.width - 40 * mm],
    )
    info_tbl.setStyle(TableStyle([
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [LIGHT, WHITE]),
        ("GRID",           (0, 0), (-1, -1), 0.3, MID),
        ("TOPPADDING",     (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 5),
        ("LEFTPADDING",    (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",   (0, 0), (-1, -1), 8),
    ]))
    story.append(info_tbl)
    story.append(Spacer(1, 5 * mm))

    # ── Pre-enrich ALL criteria explanations in parallel (1 LLM call/product) ──
    client_name = client.get("client_name", "")
    all_results = batch_result.get("results", [])
    succeeded_raw = [r for r in all_results if r.get("status") == "success"]
    succeeded = enrich_all_products(succeeded_raw, client_name)

    # ── Executive summary KPIs ────────────────────────────────────────────────
    summary   = batch_result.get("batch_summary", {})
    eligible  = [r for r in succeeded if r.get("summary", {}).get("eligibility_status") == "eligible"]
    to_review = [r for r in succeeded if r.get("summary", {}).get("eligibility_status") == "to_review"]
    not_elig  = [r for r in succeeded if r.get("summary", {}).get("eligibility_status") == "not_eligible"]

    story.append(Paragraph("Executive Summary", st["h2"]))

    kpi_row = [[
        _kpi_cell("Products Scored", str(summary.get("succeeded", 0))),
        _kpi_cell("Eligible",        str(len(eligible))),
        _kpi_cell("To Review",       str(len(to_review))),
        _kpi_cell("Not Eligible",    str(len(not_elig))),
        _kpi_cell("Duration",        f"{summary.get('duration_seconds', 0)}s"),
    ]]
    kpi_tbl = Table(kpi_row, colWidths=[doc.width / 5] * 5, rowHeights=[52])
    kpi_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), LIGHT),
        ("BOX",           (0, 0), (-1, -1), 0.5, MID),
        ("INNERGRID",     (0, 0), (-1, -1), 0.3, MID),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        # Colour accent on eligible column
        ("BACKGROUND",    (1, 0), (1, 0), colors.HexColor("#F0FDF4")),
        ("BACKGROUND",    (2, 0), (2, 0), colors.HexColor("#FFFBEB")),
        ("BACKGROUND",    (3, 0), (3, 0), colors.HexColor("#FEF2F2")),
    ]))
    story.append(kpi_tbl)
    story.append(Spacer(1, 5 * mm))

    # ── Product overview table ─────────────────────────────────────────────────
    story.append(Paragraph("Product Eligibility Overview", st["h2"]))

    sorted_results = sorted(
        succeeded,
        key=lambda r: _pct(r),
        reverse=True,
    )

    hdr = [
        Paragraph("<b>Product</b>",     st["label"]),
        Paragraph("<b>Eligibility</b>", st["label"]),
        Paragraph("<b>Score</b>",       st["label"]),
        Paragraph("<b>Points</b>",      st["label"]),
    ]
    tbl_rows = [hdr]
    for r in sorted_results:
        s    = r.get("summary", {})
        pct  = _pct(r)
        elig = s.get("eligibility_status", "not_eligible")
        ec   = _elig_color(elig)
        sc   = _score_color(pct)
        tbl_rows.append([
            Paragraph(f"<b>{r['product_id']}</b>  {r.get('product_name', '')}", st["body"]),
            Paragraph(f'<font color="#{_hex(ec)}">{_elig_label(elig)}</font>', st["body"]),
            Paragraph(f'<font color="#{_hex(sc)}"><b>{pct}%</b></font>', st["body"]),
            Paragraph(f"{s.get('total_score', 0)}/{s.get('max_score', 0)}", st["small"]),
        ])

    ov_tbl = Table(tbl_rows, colWidths=[doc.width * f for f in [0.40, 0.25, 0.18, 0.17]], repeatRows=1)
    ov_tbl.setStyle(TableStyle([
        ("BACKGROUND",     (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR",      (0, 0), (-1, 0), WHITE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT]),
        ("GRID",           (0, 0), (-1, -1), 0.3, MID),
        ("TOPPADDING",     (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 6),
        ("LEFTPADDING",    (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",   (0, 0), (-1, -1), 8),
    ]))
    story.append(ov_tbl)
    story.append(Spacer(1, 6 * mm))

    # ── Recommended products (eligible + to_review) ────────────────────────────
    priority = [r for r in sorted_results
                if r.get("summary", {}).get("eligibility_status") in ("eligible", "to_review")]
    if priority:
        story.append(Paragraph("Produits recommandés — Détail par critère", st["h2"]))
        story.append(Paragraph(
            "Pour chaque produit éligible ou à examiner, les critères d'évaluation sont présentés "
            "avec leur réponse, leur score et une explication rédigée par l'IA.",
            st["body"],
        ))
        story.append(Spacer(1, 3 * mm))
        for pr in priority:
            story.append(KeepTogether(_product_block(pr, st, doc.width)))

    # ── Not eligible products — why not ───────────────────────────────────────
    if not_elig:
        story.append(Paragraph("Produits non éligibles — Explication", st["h2"]))
        story.append(Paragraph(
            "Les produits suivants ne satisfont pas les critères d'éligibilité. "
            "Pour chaque critère en échec, une explication détaillée précise la raison du refus.",
            st["body"],
        ))
        story.append(Spacer(1, 3 * mm))
        for pr in not_elig:
            story.append(KeepTogether(_product_block(pr, st, doc.width)))

    # ── Footer ────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 4 * mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=MID))
    story.append(Spacer(1, 2 * mm))
    story.append(Paragraph(
        f"Generated by <b>Sellynx AI</b> · Leyton Group · "
        f"{datetime.today().strftime('%d %B %Y')} · Confidential — Internal use only",
        st["small"],
    ))

    doc.build(story)
    buf.seek(0)
    return buf.read()
