from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.config import get_settings
from app.models import SalesSummary


def create_sales_pdf(summary: SalesSummary, query: str) -> Path:
    settings = get_settings()
    settings.report_output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = settings.report_output_dir / f"sales_report_{timestamp}.pdf"

    doc = SimpleDocTemplate(str(path), pagesize=A4, title="Ecommerce Sales Report")
    styles = getSampleStyleSheet()
    elements = [
        Paragraph("Ecommerce Sales Report", styles["Title"]),
        Spacer(1, 12),
        Paragraph(f"Generated for query: {query}", styles["BodyText"]),
        Spacer(1, 12),
    ]

    overview = [
        ["Metric", "Value"],
        ["Date range", _date_range(summary)],
        ["Total orders", f"{summary.total_orders:,}"],
        ["Items sold", f"{summary.total_quantity:,}"],
        ["Gross revenue", f"${summary.gross_revenue:,.2f}"],
        ["Average order value", f"${summary.average_order_value:,.2f}"],
    ]
    elements.extend([_styled_table(overview), Spacer(1, 16)])

    elements.extend(_section("Top Categories", summary.top_categories))
    elements.extend(_section("Top Regions", summary.top_regions))
    elements.extend(_section("Top Products", summary.top_products))

    doc.build(elements)
    return path


def _date_range(summary: SalesSummary) -> str:
    if not summary.start_date or not summary.end_date:
        return "No sales rows found"
    return f"{summary.start_date.isoformat()} to {summary.end_date.isoformat()}"


def _section(title: str, rows: list[dict]) -> list:
    elements = [Paragraph(title, getSampleStyleSheet()["Heading2"])]
    table_rows = [["Name", "Revenue"]] + [[row["name"], f"${row['revenue']:,.2f}"] for row in rows]
    if len(table_rows) == 1:
        table_rows.append(["No data", "$0.00"])
    elements.extend([_styled_table(table_rows), Spacer(1, 16)])
    return elements


def _styled_table(rows: list[list[str]]) -> Table:
    table = Table(rows, hAlign="LEFT", colWidths=[220, 180])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f9fafb")),
                ("PADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return table
