"""
Utilidad ReportLab para exportar reportes a PDF desde el servidor.
Uso:
    response = pdf_response(
        filename="reporte.pdf",
        title="Título del Reporte",
        subtitle="Período: 01/06 – 30/06",
        headers=["Col A", "Col B", "Total"],
        rows=[["Fila1", "100", "200"]],
        totals=["TOTAL", "100", "200"],   # opcional
        landscape=False,
    )
    return response
"""

from io import BytesIO

from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape as rl_landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

# ── Paleta ────────────────────────────────────────────────────────────────────

GREEN     = colors.HexColor("#16a34a")   # green-600
GREEN_BG  = colors.HexColor("#f0fdf4")   # green-50
GRAY_HDR  = colors.HexColor("#334155")   # slate-700
GRAY_ROW  = colors.HexColor("#f8fafc")   # slate-50
GRAY_LINE = colors.HexColor("#e2e8f0")   # slate-200
WHITE     = colors.white
BLACK     = colors.HexColor("#0f172a")   # slate-900


def pdf_response(
    *,
    filename: str,
    title: str,
    subtitle: str = "",
    headers: list[str],
    rows: list[list],
    totals: list | None = None,
    landscape: bool = False,
) -> HttpResponse:
    """
    Genera un PDF con letterhead de Cantina Tita, tabla de datos y fila de totales.
    Devuelve un HttpResponse listo para retornar desde una view.
    """
    buf = BytesIO()
    pagesize = rl_landscape(A4) if landscape else A4
    margin = 18 * mm

    doc = SimpleDocTemplate(
        buf,
        pagesize=pagesize,
        leftMargin=margin,
        rightMargin=margin,
        topMargin=margin,
        bottomMargin=18 * mm,
    )

    page_w = pagesize[0] - 2 * margin
    styles = _make_styles()
    story = []

    # ── Header ────────────────────────────────────────────────────────────────
    story.append(Paragraph("La Cantina de Tita", styles["brand"]))
    story.append(Paragraph(title, styles["title"]))
    if subtitle:
        story.append(Paragraph(subtitle, styles["subtitle"]))
    story.append(Spacer(1, 6 * mm))

    # ── Table ─────────────────────────────────────────────────────────────────
    n = len(headers)
    col_w = page_w / n

    table_data = [[Paragraph(h, styles["th"]) for h in headers]]
    for row in rows:
        table_data.append([Paragraph(str(c), styles["td"]) for c in row])
    if totals:
        table_data.append([Paragraph(str(c), styles["total"]) for c in totals])

    tbl = Table(table_data, colWidths=[col_w] * n, repeatRows=1)
    tbl.setStyle(_table_style(len(rows), has_totals=bool(totals)))
    story.append(tbl)

    # ── Build ─────────────────────────────────────────────────────────────────
    doc.build(story, onFirstPage=_page_decorator, onLaterPages=_page_decorator)
    pdf = buf.getvalue()

    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


# ── Internals ─────────────────────────────────────────────────────────────────

def _make_styles() -> dict:
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

    base = getSampleStyleSheet()
    return {
        "brand": ParagraphStyle(
            "brand", parent=base["Normal"],
            fontSize=9, textColor=GREEN, fontName="Helvetica-Bold",
            spaceAfter=1 * mm,
        ),
        "title": ParagraphStyle(
            "title", parent=base["Normal"],
            fontSize=14, textColor=BLACK, fontName="Helvetica-Bold",
            spaceAfter=1 * mm,
        ),
        "subtitle": ParagraphStyle(
            "subtitle", parent=base["Normal"],
            fontSize=9, textColor=GRAY_HDR, fontName="Helvetica",
            spaceAfter=1 * mm,
        ),
        "th": ParagraphStyle(
            "th", parent=base["Normal"],
            fontSize=8, textColor=WHITE, fontName="Helvetica-Bold",
            alignment=TA_CENTER,
        ),
        "td": ParagraphStyle(
            "td", parent=base["Normal"],
            fontSize=8, textColor=BLACK, fontName="Helvetica",
            alignment=TA_LEFT, leading=10,
        ),
        "total": ParagraphStyle(
            "total", parent=base["Normal"],
            fontSize=8, textColor=WHITE, fontName="Helvetica-Bold",
            alignment=TA_LEFT,
        ),
    }


def _table_style(n_data_rows: int, has_totals: bool) -> TableStyle:
    cmds = [
        # Header row
        ("BACKGROUND",    (0, 0), (-1, 0),  GREEN),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1 if not has_totals else -2),
         [WHITE, GRAY_ROW]),
        ("GRID",          (0, 0), (-1, -1),  0.25, GRAY_LINE),
        ("TOPPADDING",    (0, 0), (-1, -1),  3),
        ("BOTTOMPADDING", (0, 0), (-1, -1),  3),
        ("LEFTPADDING",   (0, 0), (-1, -1),  4),
        ("RIGHTPADDING",  (0, 0), (-1, -1),  4),
        ("VALIGN",        (0, 0), (-1, -1),  "MIDDLE"),
    ]
    if has_totals:
        cmds += [
            ("BACKGROUND",   (0, -1), (-1, -1), GRAY_HDR),
            ("LINEABOVE",    (0, -1), (-1, -1), 1, GREEN),
        ]
    return TableStyle(cmds)


def _page_decorator(canvas, doc):
    """Pie de página con número y fecha."""
    from datetime import date
    canvas.saveState()
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(GRAY_HDR)
    w, h = doc.pagesize
    margin = doc.leftMargin
    canvas.drawString(margin, 10 * mm, f"Generado: {date.today().strftime('%d/%m/%Y')}")
    canvas.drawRightString(w - margin, 10 * mm, f"Página {doc.page}")
    canvas.restoreState()
