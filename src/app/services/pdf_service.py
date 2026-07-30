import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from ..models.transactions_model import Transaction


class PDFReceiptService:
    @staticmethod
    def generate_receipt_pdf(
        transaction: Transaction, source_acc_num: str, dest_acc_num: str
    ) -> io.BytesIO:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36,
        )
        styles = getSampleStyleSheet()

        elements = []

        # Header
        title_style = ParagraphStyle(
            "TitleStyle",
            parent=styles["Heading1"],
            fontSize=20,
            textColor=colors.HexColor("#1E3A8A"),
        )
        elements.append(
            Paragraph("FinBank - Official Transaction Receipt", title_style)
        )
        elements.append(Spacer(1, 15))

        # Data rows
        data = [
            ["Reference Number:", transaction.reference_number],
            ["Date & Time:", transaction.created_at.strftime("%Y-%m-%d %H:%M:%S UTC")],
            ["Status:", transaction.status.value],
            ["Category:", transaction.category.value],
            [
                "From Account:",
                f"****{source_acc_num[-4:]}" if source_acc_num else "N/A",
            ],
            ["To Account:", f"****{dest_acc_num[-4:]}" if dest_acc_num else "N/A"],
            ["Amount:", f"${transaction.amount:,.2f}"],
            ["Description:", transaction.description or "N/A"],
        ]

        t = Table(data, colWidths=[150, 300])
        t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
                    ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#0F172A")),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ]
            )
        )

        elements.append(t)
        doc.build(elements)
        buffer.seek(0)
        return buffer
