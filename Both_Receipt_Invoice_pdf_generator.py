import os
import random
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.lib.colors import HexColor, Color
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


class HeadlessPDFGenerator:
    def __init__(self):
        self.company_info = {
            'name': 'NextRide & Logistics',
            'address': 'No 29 Amoda Alli Street, Millennium Estate, Gbagada, Lagos, Nigeria',
            'phones': '08023428564 or 08128859763',
            'emails': 'nextflight77@gmail.com, janeagboola@yahoo.com',
            'tagline': 'Safety. Luxury. Value for Your Money.',
            'description': 'Our vehicles are well-maintained with fully functional AC for maximum comfort. We offer rentals—daily, weekly, or monthly—backed by professional and courteous drivers. Enjoy interstate travel with peace of mind, knowing you\'re in safe hands.',
            'footer': 'Copyright © 2025 | Invoice powered by Opygoal Technology Ltd. | Developer: Oladotun Ajakaiye, Service Manager & Data Analyst',
            'bank_details': 'Bank: Sterling Bank | Account No: 0123186628'
        }

        self.logo_path = 'static/logo.png'  # Default permanent logo path
        self.signature_path = 'static/signature.png'  # Default permanent signature path
        self.naira_font_name = 'Helvetica'
        self.has_naira_font = False  # Always use 'N'

    def set_paths(self, logo_path=None, signature_path=None):
        if logo_path and os.path.exists(logo_path):
            self.logo_path = logo_path
        if signature_path and os.path.exists(signature_path):
            self.signature_path = signature_path

    def add_watermark_hologram(self, canvas_obj, doc, text_to_watermark):
        canvas_obj.saveState()
        canvas_obj.setFillColor(Color(0.2, 0.6, 0.8, alpha=0.15))
        canvas_obj.setStrokeColor(Color(0.2, 0.6, 0.8, alpha=0.15))
        for x in range(0, int(doc.pagesize[0]), 120):
            for y in range(0, int(doc.pagesize[1]), 100):
                canvas_obj.saveState()
                canvas_obj.translate(x, y)
                canvas_obj.rotate(45)
                canvas_obj.setFont("Helvetica-Bold", 20)
                canvas_obj.drawString(0, 0, text_to_watermark)
                canvas_obj.restoreState()
        canvas_obj.restoreState()

    def generate_invoice_pdf(self, output_path, client_info, trip_info, service_info, notes):
        doc = SimpleDocTemplate(output_path, pagesize=A4,
                                rightMargin=12, leftMargin=12,  # Reduced margins for mobile
                                topMargin=12, bottomMargin=12)
        elements = []
        styles = getSampleStyleSheet()

        normal_font = self.naira_font_name
        bold_font = 'Helvetica-Bold'

        primary_blue = HexColor('#3498db')
        light_gray = HexColor('#ecf0f1')
        medium_gray = HexColor('#bdc3c7')
        dark_text = HexColor('#2c3e50')
        light_yellow = HexColor('#fff9e6')
        yellow_border = HexColor('#ffe6b3')

        # --- Styles (reduced for mobile readability) ---
        company_name_style = ParagraphStyle('CompanyNameStyle', parent=styles['Normal'],
                                           fontName=bold_font, fontSize=16,  # Reduced from 18
                                           textColor=primary_blue, alignment=0, spaceAfter=2)  # Left-aligned
        company_address_style = ParagraphStyle('CompanyAddressStyle', parent=styles['Normal'],
                                              fontName=normal_font, fontSize=7,  # Reduced from 8
                                              textColor=dark_text, alignment=0, spaceAfter=2)
        company_contact_style = ParagraphStyle('CompanyContactStyle', parent=styles['Normal'],
                                              fontName=normal_font, fontSize=7,  # Reduced from 8
                                              textColor=dark_text, alignment=0, spaceAfter=4)

        invoice_title_style = ParagraphStyle('InvoiceTitleStyle', parent=styles['Heading1'],
                                            fontName=bold_font, fontSize=20,  # Reduced from 24
                                            textColor=primary_blue, alignment=1, spaceAfter=15)  # Reduced from 20
        section_header_style = ParagraphStyle('SectionHeaderStyle', parent=styles['Heading2'],
                                             fontName=bold_font, fontSize=10,
                                             textColor=colors.white, backColor=primary_blue,
                                             alignment=0, spaceBefore=8, spaceAfter=4,  # Reduced spacing
                                             leftIndent=5, rightIndent=5, borderPadding=3)
        details_content_style = ParagraphStyle('DetailsContentStyle', parent=styles['Normal'],
                                              fontName=normal_font, fontSize=8,  # Reduced from 9
                                              textColor=dark_text, spaceAfter=2)
        table_header_style = ParagraphStyle('TableHeaderStyle', parent=styles['Normal'],
                                           fontName=bold_font, fontSize=8,  # Reduced from 9
                                           textColor=colors.white, alignment=1)
        table_cell_style = ParagraphStyle('TableCellStyle', parent=styles['Normal'],
                                         fontName=normal_font, fontSize=8,  # Reduced from 9
                                         textColor=dark_text, alignment=0)
        total_label_style = ParagraphStyle('TotalLabelStyle', parent=styles['Normal'],
                                          fontName=bold_font, fontSize=9,  # Reduced from 10
                                          textColor=dark_text, alignment=2)
        total_amount_style = ParagraphStyle('TotalAmountStyle', parent=styles['Normal'],
                                           fontName=bold_font, fontSize=9,  # Reduced from 10
                                           textColor=primary_blue, alignment=2)

        # --- Header with logo on left ---
        header_data = [
            [Paragraph(self.company_info['name'], company_name_style)],
            [Paragraph(self.company_info['address'], company_address_style)],
            [Paragraph(f"Phones: {self.company_info['phones']}", company_contact_style)],
            [Paragraph(f"Emails: {self.company_info['emails']}", company_contact_style)],
        ]

        if self.logo_path and os.path.exists(self.logo_path):
            header_table = Table([
                [Image(self.logo_path, width=1.2 * inch, height=0.6 * inch),
                 Table(header_data, colWidths=[4.5 * inch], style=TableStyle([
                     ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                     ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                 ]))]
            ], colWidths=[1.2 * inch, 4.8 * inch])  # Adjusted for better fit
            header_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
        else:
            header_table = Table(header_data, colWidths=[6 * inch])
            header_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ]))
        elements.append(header_table)
        elements.append(Spacer(1, 8))  # Reduced from 10

        # --- Invoice Info ---
        invoice_info_data = [
            [Paragraph("INVOICE", invoice_title_style)],
            [Paragraph(f"Invoice No: <b>{client_info['invoice_number']}</b>", details_content_style)],
            [Paragraph(f"Date: <b>{client_info['invoice_date']}</b>", details_content_style)],
        ]
        invoice_info_table = Table(invoice_info_data, colWidths=[6 * inch])
        invoice_info_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        elements.append(invoice_info_table)
        elements.append(Spacer(1, 8))  # Reduced from 10

        # --- Bill To ---
        elements.append(Paragraph("BILL TO:", section_header_style))
        client_data = [
            [Paragraph("<b>Name:</b>", details_content_style), Paragraph(client_info['name'], details_content_style)],
            [Paragraph("<b>Address:</b>", details_content_style), Paragraph(client_info['address'], details_content_style)],
            [Paragraph("<b>Contact:</b>", details_content_style), Paragraph(client_info['contact'], details_content_style)],
        ]
        client_table = Table(client_data, colWidths=[1.2 * inch, 4.8 * inch])  # Reduced from 1.5, 4.5
        client_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), light_gray),
            ('GRID', (0, 0), (-1, -1), 0.5, medium_gray),
            ('PADDING', (0, 0), (-1, -1), 4),  # Reduced padding
        ]))
        elements.append(client_table)
        elements.append(Spacer(1, 8))  # Reduced from 10

        # --- Trip Details ---
        elements.append(Paragraph("TRIP DETAILS:", section_header_style))
        trip_data = [
            [Paragraph("<b>Trip Type:</b>", details_content_style), Paragraph(trip_info['trip_type'], details_content_style)],
            [Paragraph("<b>Pickup Point:</b>", details_content_style), Paragraph(trip_info['pickup_point'], details_content_style)],
            [Paragraph("<b>Drop Off Point:</b>", details_content_style), Paragraph(trip_info['dropoff_point'], details_content_style)],
            [Paragraph("<b>Trip Date:</b>", details_content_style), Paragraph(trip_info['trip_date'], details_content_style)],
        ]
        if trip_info.get('return_date'):
            trip_data.append([Paragraph("<b>Return Date:</b>", details_content_style), Paragraph(trip_info['return_date'], details_content_style)])
        trip_table = Table(trip_data, colWidths=[1.2 * inch, 4.8 * inch])  # Reduced from 1.5, 4.5
        trip_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), light_gray),
            ('GRID', (0, 0), (-1, -1), 0.5, medium_gray),
            ('PADDING', (0, 0), (-1, -1), 4),  # Reduced padding
        ]))
        elements.append(trip_table)
        elements.append(Spacer(1, 8))  # Reduced from 10

        # --- Services ---
        elements.append(Paragraph("SERVICES:", section_header_style))
        currency_symbol = 'N'  # Since has_naira_font is False
        services_data = [
            [Paragraph('Description', table_header_style),
             Paragraph('Qty', table_header_style),
             Paragraph(f'Price ({currency_symbol})', table_header_style),
             Paragraph(f'Amount ({currency_symbol})', table_header_style)],
            [Paragraph(service_info['description'], table_cell_style),
             Paragraph(str(service_info['quantity']), table_cell_style),
             Paragraph(f"{service_info['price']:,.2f}", table_cell_style),
             Paragraph(f"{service_info['amount']:,.2f}", table_cell_style)],
            ['', '', Paragraph('<b>TOTAL:</b>', total_label_style),
             Paragraph(f'<b>{currency_symbol}{service_info["amount"]:,.2f}</b>', total_amount_style)]
        ]
        services_table = Table(services_data, colWidths=[3 * inch, 0.6 * inch, 0.8 * inch, 0.8 * inch])  # Reduced widths
        services_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), primary_blue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), bold_font),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 5),  # Reduced from 6
            ('BACKGROUND', (0, 1), (-1, 1), light_gray),
            ('GRID', (0, 0), (-1, -1), 0.5, medium_gray),
            ('ALIGN', (0, 0), (0, 1), 'LEFT'),
            ('ALIGN', (1, 1), (1, 1), 'CENTER'),
            ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('SPAN', (0, 2), (1, 2)),
            ('BACKGROUND', (0, 2), (-1, 2), light_gray),
            ('TEXTCOLOR', (2, 2), (2, 2), dark_text),
            ('TEXTCOLOR', (3, 2), (3, 2), primary_blue),
            ('FONTNAME', (2, 2), (3, 2), bold_font),
        ]))
        elements.append(services_table)
        elements.append(Spacer(1, 8))  # Reduced from 10

        # --- Additional Notes ---
        elements.append(Paragraph("ADDITIONAL NOTES:", section_header_style))
        notes_paragraph = Paragraph(notes, details_content_style)
        notes_table = Table([[notes_paragraph]], colWidths=[6 * inch])
        notes_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), light_yellow),
            ('GRID', (0, 0), (-1, -1), 0.5, yellow_border),
            ('PADDING', (0, 0), (-1, -1), 4),  # Reduced from 5
        ]))
        elements.append(notes_table)
        elements.append(Spacer(1, 8))  # Reduced from 10

        # --- Signature (if available) ---
        if self.signature_path and os.path.exists(self.signature_path):
            elements.append(Image(self.signature_path, width=1.8 * inch, height=0.4 * inch))  # Reduced size
            elements.append(Spacer(1, 6))  # Reduced from 10

        # --- Footer ---
        elements.append(Paragraph(f"<b>Account Details:</b> {self.company_info['bank_details']}", details_content_style))
        elements.append(Paragraph("Thank you for your patronage!", details_content_style))
        elements.append(Paragraph(f"■ {self.company_info['tagline']} ■", details_content_style))
        elements.append(Paragraph(self.company_info['description'], details_content_style))

        # --- Build PDF ---
        def add_page_elements(canvas_obj, doc):
            self.add_watermark_hologram(canvas_obj, doc, "NextRide & Logistics")
            canvas_obj.setFont(normal_font, 5)  # Reduced from 6
            canvas_obj.setFillColor(colors.grey)
            canvas_obj.drawString(doc.leftMargin, 10, self.company_info['footer'])

        doc.build(elements, onFirstPage=add_page_elements, onLaterPages=add_page_elements)
        print(f"Invoice saved as {output_path}")


if __name__ == "__main__":
    generator = HeadlessPDFGenerator()

    invoice_client_info = {
        'name': 'Mrs Adeola Ajibadade',
        'address': 'Ibadan',
        'contact': 'n/a',
        'invoice_number': f"INV-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}",
        'invoice_date': datetime.now().strftime('%B %d, %Y')
    }
    invoice_trip_info = {
        'trip_type': 'Single Trip',
        'pickup_point': 'Ibadan',
        'dropoff_point': 'Lekki Phase 1',
        'trip_date': 'September 11, 2025',
        'return_date': 'September 13, 2025'
    }
    invoice_service_info = {
        'description': 'Interstate transportation service with Prado Jeep (2013)',
        'quantity': 1,
        'price': 250000.00,
        'amount': 250000.00
    }
    invoice_notes = "Comprehensive interstate transportation service for Mrs Adeola Ajibadade."

    generator.generate_invoice_pdf('sample_invoice.pdf', invoice_client_info, invoice_trip_info,
                                   invoice_service_info, invoice_notes)