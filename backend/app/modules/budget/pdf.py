"""Budget PDF generation service."""

import hashlib
from datetime import date
from decimal import Decimal
from io import BytesIO
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.core.auth.models import Clinic

from .models import Budget


class BudgetPDFService:
    """Service for generating budget PDFs.

    MVP: Generates simple HTML-based PDF.
    Future: Integration with professional PDF templates.
    """

    @staticmethod
    def generate_pdf(
        budget: Budget,
        clinic: "Clinic",
        is_preview: bool = False,
        locale: str = "es",
    ) -> bytes:
        """Generate PDF for a budget.

        Args:
            budget: The budget to generate PDF for
            clinic: The clinic for branding
            is_preview: If True, adds DRAFT watermark
            locale: Language for labels (es/en)

        Returns:
            PDF content as bytes
        """
        # Generate HTML content
        html_content = BudgetPDFService._generate_html(budget, clinic, is_preview, locale)

        # Convert to PDF
        pdf_bytes = BudgetPDFService._html_to_pdf(html_content)

        return pdf_bytes

    @staticmethod
    def generate_pdf_hash(pdf_bytes: bytes) -> str:
        """Generate SHA-256 hash of PDF content for signature verification."""
        return hashlib.sha256(pdf_bytes).hexdigest()

    @staticmethod
    def _generate_html(
        budget: Budget,
        clinic: "Clinic",
        is_preview: bool,
        locale: str,
    ) -> str:
        """Generate HTML content for the budget."""
        # Localized labels
        labels = BudgetPDFService._get_labels(locale)

        # Format currency
        def format_currency(amount: Decimal) -> str:
            return f"{amount:,.2f} {budget.currency}"

        # Build items table rows
        items_html = ""
        for i, item in enumerate(budget.items, 1):
            # Get item name from catalog
            item_name = ""
            if item.catalog_item:
                item_name = item.catalog_item.names.get(locale, "")
                if not item_name:
                    # Fallback to first available name
                    item_name = next(iter(item.catalog_item.names.values()), "")

            tooth_info = ""
            if item.tooth_number:
                tooth_info = f"#{item.tooth_number}"
                if item.surfaces:
                    tooth_info += f" ({', '.join(item.surfaces)})"

            items_html += f"""
            <tr>
                <td class="number">{i}</td>
                <td class="description">
                    {item_name}
                    {f'<br><small class="tooth">{tooth_info}</small>' if tooth_info else ""}
                    {f'<br><small class="notes">{item.notes}</small>' if item.notes else ""}
                </td>
                <td class="quantity">{item.quantity}</td>
                <td class="price">{format_currency(item.unit_price)}</td>
                {f'<td class="discount">{format_currency(item.line_discount)}</td>' if item.line_discount else '<td class="discount">-</td>'}
                <td class="total">{format_currency(item.line_total)}</td>
            </tr>
            """

        # Status badge
        status_label = labels["status"].get(budget.status, budget.status)

        # Watermark for preview
        watermark_style = ""
        watermark_html = ""
        if is_preview or budget.status == "draft":
            watermark_style = """
            .watermark {
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%) rotate(-45deg);
                font-size: 120px;
                color: rgba(200, 200, 200, 0.3);
                z-index: 1000;
                pointer-events: none;
            }
            """
            watermark_html = f'<div class="watermark">{labels["draft"]}</div>'

        # Patient info
        patient_name = ""
        if budget.patient:
            patient_name = f"{budget.patient.first_name} {budget.patient.last_name}"

        # Professional info
        professional_name = ""
        if budget.assigned_professional:
            professional_name = f"{budget.assigned_professional.first_name} {budget.assigned_professional.last_name}"

        # Validity period
        valid_from = budget.valid_from.strftime("%d/%m/%Y") if budget.valid_from else "-"
        valid_until = (
            budget.valid_until.strftime("%d/%m/%Y") if budget.valid_until else labels["no_expiry"]
        )

        # Build HTML
        html = f"""
        <!DOCTYPE html>
        <html lang="{locale}">
        <head>
            <meta charset="UTF-8">
            <title>{labels["budget"]} {budget.budget_number}</title>
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                body {{
                    font-family: 'Helvetica Neue', Arial, sans-serif;
                    font-size: 11pt;
                    line-height: 1.4;
                    color: #333;
                    padding: 20mm;
                }}
                {watermark_style}
                .header {{
                    display: flex;
                    justify-content: space-between;
                    margin-bottom: 30px;
                    padding-bottom: 20px;
                    border-bottom: 2px solid #2563eb;
                }}
                .clinic-info {{
                    max-width: 60%;
                }}
                .clinic-name {{
                    font-size: 18pt;
                    font-weight: bold;
                    color: #1e40af;
                    margin-bottom: 5px;
                }}
                .clinic-details {{
                    font-size: 9pt;
                    color: #666;
                }}
                .budget-info {{
                    text-align: right;
                }}
                .budget-number {{
                    font-size: 14pt;
                    font-weight: bold;
                    color: #1e40af;
                }}
                .budget-meta {{
                    font-size: 9pt;
                    color: #666;
                    margin-top: 5px;
                }}
                .status-badge {{
                    display: inline-block;
                    padding: 3px 10px;
                    border-radius: 12px;
                    font-size: 9pt;
                    font-weight: bold;
                    text-transform: uppercase;
                    margin-top: 8px;
                }}
                .status-draft {{ background: #e5e7eb; color: #374151; }}
                .status-sent {{ background: #dbeafe; color: #1e40af; }}
                .status-accepted {{ background: #d1fae5; color: #065f46; }}
                .status-rejected {{ background: #fee2e2; color: #991b1b; }}
                .status-expired {{ background: #fef3c7; color: #92400e; }}

                .section {{
                    margin-bottom: 25px;
                }}
                .section-title {{
                    font-size: 11pt;
                    font-weight: bold;
                    color: #1e40af;
                    margin-bottom: 10px;
                    padding-bottom: 5px;
                    border-bottom: 1px solid #e5e7eb;
                }}
                .patient-info {{
                    display: flex;
                    gap: 40px;
                }}
                .info-group {{
                    min-width: 200px;
                }}
                .info-label {{
                    font-size: 9pt;
                    color: #666;
                    margin-bottom: 2px;
                }}
                .info-value {{
                    font-weight: 500;
                }}

                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-bottom: 20px;
                }}
                th {{
                    background: #f3f4f6;
                    padding: 10px 8px;
                    text-align: left;
                    font-size: 9pt;
                    font-weight: 600;
                    color: #374151;
                    border-bottom: 2px solid #e5e7eb;
                }}
                td {{
                    padding: 10px 8px;
                    border-bottom: 1px solid #e5e7eb;
                    vertical-align: top;
                }}
                tr:last-child td {{
                    border-bottom: none;
                }}
                .number {{ width: 30px; text-align: center; }}
                .description {{ width: auto; }}
                .quantity {{ width: 60px; text-align: center; }}
                .price {{ width: 100px; text-align: right; }}
                .discount {{ width: 100px; text-align: right; color: #059669; }}
                .total {{ width: 100px; text-align: right; font-weight: 500; }}
                .tooth {{ color: #6b7280; }}
                .notes {{ color: #9ca3af; font-style: italic; }}

                .totals {{
                    float: right;
                    width: 300px;
                    margin-top: 20px;
                }}
                .totals table {{
                    margin-bottom: 0;
                }}
                .totals td {{
                    padding: 6px 8px;
                    border-bottom: none;
                }}
                .totals .label {{
                    text-align: left;
                    color: #666;
                }}
                .totals .value {{
                    text-align: right;
                    font-weight: 500;
                }}
                .totals .grand-total {{
                    font-size: 14pt;
                    font-weight: bold;
                    color: #1e40af;
                    border-top: 2px solid #1e40af;
                    padding-top: 10px;
                }}

                .notes-section {{
                    clear: both;
                    padding-top: 30px;
                    margin-top: 30px;
                    border-top: 1px solid #e5e7eb;
                }}
                .notes-content {{
                    background: #f9fafb;
                    padding: 15px;
                    border-radius: 8px;
                    font-size: 10pt;
                    color: #4b5563;
                }}

                .validity {{
                    margin-top: 20px;
                    padding: 15px;
                    background: #eff6ff;
                    border-radius: 8px;
                    font-size: 10pt;
                }}
                .validity strong {{
                    color: #1e40af;
                }}

                .signature-section {{
                    margin-top: 40px;
                    padding-top: 20px;
                }}
                .signature-box {{
                    display: inline-block;
                    width: 45%;
                    margin-right: 5%;
                }}
                .signature-line {{
                    border-bottom: 1px solid #333;
                    height: 50px;
                    margin-bottom: 5px;
                }}
                .signature-label {{
                    font-size: 9pt;
                    color: #666;
                }}

                .footer {{
                    position: fixed;
                    bottom: 15mm;
                    left: 20mm;
                    right: 20mm;
                    font-size: 8pt;
                    color: #9ca3af;
                    text-align: center;
                    border-top: 1px solid #e5e7eb;
                    padding-top: 10px;
                }}

                @media print {{
                    body {{ padding: 0; }}
                    .footer {{ position: fixed; }}
                }}
            </style>
        </head>
        <body>
            {watermark_html}

            <div class="header">
                <div class="clinic-info">
                    <div class="clinic-name">{clinic.name if clinic else "Dental Clinic"}</div>
                    <div class="clinic-details">
                        {
            clinic.address if hasattr(clinic, "address") and clinic.address else ""
        }<br>
                        {clinic.phone if hasattr(clinic, "phone") and clinic.phone else ""}
                        {f" | {clinic.email}" if hasattr(clinic, "email") and clinic.email else ""}
                    </div>
                </div>
                <div class="budget-info">
                    <div class="budget-number">{labels["budget"]} {budget.budget_number}</div>
                    <div class="budget-meta">
                        {labels["version"]}: {budget.version}<br>
                        {labels["date"]}: {budget.created_at.strftime("%d/%m/%Y")}
                    </div>
                    <span class="status-badge status-{budget.status}">{status_label}</span>
                </div>
            </div>

            <div class="section">
                <div class="section-title">{labels["patient_info"]}</div>
                <div class="patient-info">
                    <div class="info-group">
                        <div class="info-label">{labels["patient"]}</div>
                        <div class="info-value">{patient_name}</div>
                    </div>
                    {
            f'''
                    <div class="info-group">
                        <div class="info-label">{labels["professional"]}</div>
                        <div class="info-value">{professional_name}</div>
                    </div>
                    '''
            if professional_name
            else ""
        }
                </div>
            </div>

            <div class="section">
                <div class="section-title">{labels["treatments"]}</div>
                <table>
                    <thead>
                        <tr>
                            <th class="number">#</th>
                            <th class="description">{labels["description"]}</th>
                            <th class="quantity">{labels["qty"]}</th>
                            <th class="price">{labels["unit_price"]}</th>
                            <th class="discount">{labels["discount"]}</th>
                            <th class="total">{labels["total"]}</th>
                        </tr>
                    </thead>
                    <tbody>
                        {items_html}
                    </tbody>
                </table>

                <div class="totals">
                    <table>
                        <tr>
                            <td class="label">{labels["subtotal"]}:</td>
                            <td class="value">{format_currency(budget.subtotal)}</td>
                        </tr>
                        {
            f'''
                        <tr>
                            <td class="label">{labels["total_discount"]}:</td>
                            <td class="value discount">-{format_currency(budget.total_discount)}</td>
                        </tr>
                        '''
            if budget.total_discount
            else ""
        }
                        {
            f'''
                        <tr>
                            <td class="label">{labels["tax"]}:</td>
                            <td class="value">{format_currency(budget.total_tax)}</td>
                        </tr>
                        '''
            if budget.total_tax
            else ""
        }
                        <tr>
                            <td class="label grand-total">{labels["grand_total"]}:</td>
                            <td class="value grand-total">{format_currency(budget.total)}</td>
                        </tr>
                    </table>
                </div>
            </div>

            <div class="validity">
                <strong>{labels["validity"]}:</strong>
                {labels["from"]} {valid_from} {labels["until"]} {valid_until}
            </div>

            {
            f'''
            <div class="notes-section">
                <div class="section-title">{labels["notes"]}</div>
                <div class="notes-content">{budget.patient_notes}</div>
            </div>
            '''
            if budget.patient_notes
            else ""
        }

            <div class="signature-section">
                <div class="signature-box">
                    <div class="signature-line"></div>
                    <div class="signature-label">{labels["patient_signature"]}</div>
                </div>
                <div class="signature-box">
                    <div class="signature-line"></div>
                    <div class="signature-label">{labels["clinic_signature"]}</div>
                </div>
            </div>

            <div class="footer">
                {labels["generated_by"]} DentalPin | {date.today().strftime("%d/%m/%Y %H:%M")}
            </div>
        </body>
        </html>
        """

        return html

    @staticmethod
    def _html_to_pdf(html_content: str) -> bytes:
        """Convert HTML to PDF.

        Uses WeasyPrint if available, otherwise returns HTML as fallback.
        """
        try:
            from weasyprint import HTML

            pdf_buffer = BytesIO()
            HTML(string=html_content).write_pdf(pdf_buffer)
            return pdf_buffer.getvalue()
        except ImportError:
            # WeasyPrint not installed, return HTML content
            # In production, WeasyPrint should be installed
            return html_content.encode("utf-8")

    @staticmethod
    def _get_labels(locale: str) -> dict:
        """Get localized labels for PDF."""
        labels_es = {
            "budget": "Presupuesto",
            "version": "Versión",
            "date": "Fecha",
            "draft": "BORRADOR",
            "patient_info": "Información del Paciente",
            "patient": "Paciente",
            "professional": "Profesional",
            "treatments": "Tratamientos",
            "description": "Descripción",
            "qty": "Cant.",
            "unit_price": "Precio Unit.",
            "discount": "Descuento",
            "total": "Total",
            "subtotal": "Subtotal",
            "total_discount": "Descuento total",
            "tax": "IVA",
            "grand_total": "TOTAL",
            "validity": "Validez",
            "from": "desde",
            "until": "hasta",
            "no_expiry": "sin fecha de caducidad",
            "notes": "Observaciones",
            "patient_signature": "Firma del Paciente",
            "clinic_signature": "Firma de la Clínica",
            "generated_by": "Generado por",
            "status": {
                "draft": "Borrador",
                "sent": "Enviado",
                "partially_accepted": "Aceptado Parcial",
                "accepted": "Aceptado",
                "in_progress": "En Progreso",
                "completed": "Completado",
                "invoiced": "Facturado",
                "rejected": "Rechazado",
                "expired": "Caducado",
                "cancelled": "Cancelado",
            },
        }

        labels_en = {
            "budget": "Quote",
            "version": "Version",
            "date": "Date",
            "draft": "DRAFT",
            "patient_info": "Patient Information",
            "patient": "Patient",
            "professional": "Professional",
            "treatments": "Treatments",
            "description": "Description",
            "qty": "Qty",
            "unit_price": "Unit Price",
            "discount": "Discount",
            "total": "Total",
            "subtotal": "Subtotal",
            "total_discount": "Total discount",
            "tax": "VAT",
            "grand_total": "TOTAL",
            "validity": "Validity",
            "from": "from",
            "until": "until",
            "no_expiry": "no expiry date",
            "notes": "Notes",
            "patient_signature": "Patient Signature",
            "clinic_signature": "Clinic Signature",
            "generated_by": "Generated by",
            "status": {
                "draft": "Draft",
                "sent": "Sent",
                "partially_accepted": "Partially Accepted",
                "accepted": "Accepted",
                "in_progress": "In Progress",
                "completed": "Completed",
                "invoiced": "Invoiced",
                "rejected": "Rejected",
                "expired": "Expired",
                "cancelled": "Cancelled",
            },
        }

        return labels_es if locale == "es" else labels_en
