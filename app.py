from flask import Flask, render_template, request, send_file
import os
import random
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['STATIC_FOLDER'] = 'static'  # Define static folder for default images
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Default logo and signature paths
DEFAULT_LOGO_PATH = os.path.join(app.config['STATIC_FOLDER'], 'logo.png')
DEFAULT_SIGNATURE_PATH = os.path.join(app.config['STATIC_FOLDER'], 'signature.png')

# Initialize company info
company_info = {
    'name': 'NextRide & Logistics',
    'address': 'No 29 Amoda Alli Street, Millennium Estate, Gbagada, Lagos, Nigeria',
    'phones': '08023428564 or 08128859763',
    'emails': 'nextflight77@gmail.com, janeagboola@yahoo.com',
    'tagline': 'Safety. Luxury. Value for Your Money.',
    'description': 'Our vehicles are well-maintained with fully functional AC for maximum comfort. We offer rentals—daily, weekly, or monthly—backed by professional and courteous drivers. Enjoy interstate travel with peace of mind, knowing you\'re in safe hands.',
    'footer': 'Copyright © 2025 | Invoice powered by Opygoal Technology Ltd. | Developer: Oladotun Ajakaiye, Service Manager & Data Analyst',
    'bank_details': 'Bank: Sterling Bank | Account No: 0123186628'
}

# Font Registration for Naira Symbol
dejavu_font_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'DejaVuSans.ttf')
naira_font_name = 'Helvetica'
has_naira_font = False

try:
    if os.path.exists(dejavu_font_path):
        pdfmetrics.registerFont(TTFont('DejaVuSans', dejavu_font_path))
        naira_font_name = 'DejaVuSans'
        has_naira_font = True
        print(f"INFO: Successfully registered DejaVuSans font from: {dejavu_font_path}")
    else:
        print(f"WARNING: DejaVuSans.ttf not found at {dejavu_font_path}. Naira sign might not display correctly. Using Helvetica.")
except Exception as e:
    print(f"ERROR: Could not register DejaVuSans font ({e}). Naira sign might not display correctly. Using Helvetica.")

def add_watermark_hologram(canvas_obj, doc, text_to_watermark):
    canvas_obj.saveState()
    canvas_obj.setFillColor(colors.lightblue)
    canvas_obj.setStrokeColor(colors.lightblue)
    watermark_text = text_to_watermark

    for x in range(0, int(doc.pagesize[0]), 120):
        for y in range(0, int(doc.pagesize[1]), 100):
            canvas_obj.saveState()
            canvas_obj.translate(x, y)
            canvas_obj.rotate(45)
            canvas_obj.setFont("Helvetica-Bold", 20)
            canvas_obj.setFillAlpha(0.1)
            canvas_obj.drawString(0, 0, watermark_text)
            canvas_obj.restoreState()
    canvas_obj.restoreState()

def generate_invoice_pdf(output_path, client_info, trip_info, service_info, notes, logo_path=None, signature_path=None):
    doc = SimpleDocTemplate(output_path, pagesize=A4,
                            rightMargin=15, leftMargin=15,
                            topMargin=15, bottomMargin=15)
    elements = []
    styles = getSampleStyleSheet()

    normal_font = naira_font_name
    bold_font = 'Helvetica-Bold' if normal_font == 'Helvetica' else f'{naira_font_name}-Bold'

    primary_blue = HexColor('#3498db')
    light_gray = HexColor('#ecf0f1')
    medium_gray = HexColor('#bdc3c7')
    dark_text = HexColor('#2c3e50')
    light_yellow = HexColor('#fff9e6')
    yellow_border = HexColor('#ffe6b3')

    company_name_style = ParagraphStyle('CompanyNameStyle', parent=styles['Normal'],
                                       fontName=bold_font, fontSize=18, textColor=primary_blue,
                                       alignment=0, spaceAfter=2)
    company_address_style = ParagraphStyle('CompanyAddressStyle', parent=styles['Normal'],
                                           fontName=normal_font, fontSize=8, textColor=dark_text,
                                           alignment=0, spaceAfter=2)
    company_contact_style = ParagraphStyle('CompanyContactStyle', parent=styles['Normal'],
                                           fontName=normal_font, fontSize=8, textColor=dark_text,
                                           alignment=0, spaceAfter=4)

    invoice_title_style = ParagraphStyle('InvoiceTitleStyle', parent=styles['Heading1'],
                                        fontName=bold_font, fontSize=24, textColor=primary_blue,
                                        alignment=1, spaceAfter=20)
    section_header_style = ParagraphStyle('SectionHeaderStyle', parent=styles['Heading2'],
                                          fontName=bold_font, fontSize=10, textColor=colors.white,
                                          backColor=primary_blue, alignment=0, spaceBefore=10,
                                          spaceAfter=5, leftIndent=5, rightIndent=5, borderPadding=3)
    details_content_style = ParagraphStyle('DetailsContentStyle', parent=styles['Normal'],
                                           fontName=normal_font, fontSize=9, textColor=dark_text,
                                           spaceAfter=2)
    table_header_style = ParagraphStyle('TableHeaderStyle', parent=styles['Normal'],
                                       fontName=bold_font, fontSize=9, textColor=colors.white,
                                       alignment=1)
    table_cell_style = ParagraphStyle('TableCellStyle', parent=styles['Normal'],
                                     fontName=normal_font, fontSize=9, textColor=dark_text,
                                     alignment=0)
    total_label_style = ParagraphStyle('TotalLabelStyle', parent=styles['Normal'],
                                      fontName=bold_font, fontSize=10, textColor=dark_text,
                                      alignment=2)
    total_amount_style = ParagraphStyle('TotalAmountStyle', parent=styles['Normal'],
                                       fontName=bold_font, fontSize=10, textColor=primary_blue,
                                       alignment=2)
    footer_bank_style = ParagraphStyle('FooterBankStyle', parent=styles['Normal'],
                                      fontName=bold_font, fontSize=9, textColor=dark_text,
                                      alignment=1, spaceBefore=10, spaceAfter=2)
    footer_thankyou_style = ParagraphStyle('FooterThankYouStyle', parent=styles['Normal'],
                                           fontName=normal_font, fontSize=10, textColor=dark_text,
                                           alignment=1, spaceAfter=2)
    footer_tagline_style = ParagraphStyle('FooterTaglineStyle', parent=styles['Normal'],
                                          fontName=bold_font, fontSize=8, textColor=primary_blue,
                                          alignment=1, spaceAfter=2)
    footer_description_style = ParagraphStyle('FooterDescriptionStyle', parent=styles['Normal'],
                                             fontName=normal_font, fontSize=7, textColor=dark_text,
                                             alignment=1, spaceAfter=10)
    footer_copyright_style = ParagraphStyle('FooterCopyrightStyle', parent=styles['Normal'],
                                            fontName=normal_font, fontSize=6, textColor=colors.grey,
                                            alignment=1, spaceBefore=5)

    def add_page_elements(canvas_obj, doc):
        add_watermark_hologram(canvas_obj, doc, "NextRide & Logistics")
        canvas_obj.saveState()
        canvas_obj.setFont(normal_font, 6)
        canvas_obj.setFillColor(colors.grey)
        canvas_obj.drawString(doc.leftMargin, 10, company_info['footer'])
        canvas_obj.restoreState()

    # Header with default or uploaded logo on the left
    header_data = []
    logo_path = logo_path if logo_path and os.path.exists(logo_path) else DEFAULT_LOGO_PATH if os.path.exists(DEFAULT_LOGO_PATH) else None
    if logo_path:
        header_data.append([Image(logo_path, width=1.5*inch, height=1.5*inch),
                           Table([[Paragraph(company_info['name'], company_name_style)],
                                  [Paragraph(company_info['address'], company_address_style)],
                                  [Paragraph(f"Phones: {company_info['phones']}", company_contact_style)],
                                  [Paragraph(f"Emails: {company_info['emails']}", company_contact_style)]],
                                 colWidths=[4.5*inch], style=TableStyle([
                                     ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                     ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                                 ]))])
    else:
        header_data.append([Table([[Paragraph(company_info['name'], company_name_style)],
                                  [Paragraph(company_info['address'], company_address_style)],
                                  [Paragraph(f"Phones: {company_info['phones']}", company_contact_style)],
                                  [Paragraph(f"Emails: {company_info['emails']}", company_contact_style)]],
                                 colWidths=[6*inch], style=TableStyle([
                                     ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                     ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                                 ]))])

    header_table = Table(header_data, colWidths=[1.5*inch, 4.5*inch] if logo_path else [6*inch])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))

    elements.append(header_table)
    elements.append(Spacer(1, 10))

    invoice_info_data = [
        [Paragraph("INVOICE", invoice_title_style)],
        [Paragraph(f"Invoice No: <b>{client_info['invoice_number']}</b>", details_content_style)],
        [Paragraph(f"Date: <b>{client_info['invoice_date']}</b>", details_content_style)],
    ]
    invoice_info_table = Table(invoice_info_data, colWidths=[6*inch])
    invoice_info_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    elements.append(invoice_info_table)
    elements.append(Spacer(1, 10))

    elements.append(Paragraph("BILL TO:", section_header_style))
    client_data = [
        [Paragraph(f"<b>Name:</b>", details_content_style), Paragraph(client_info['name'], details_content_style)],
        [Paragraph(f"<b>Address:</b>", details_content_style), Paragraph(client_info['address'], details_content_style)],
        [Paragraph(f"<b>Contact:</b>", details_content_style), Paragraph(client_info['contact'], details_content_style)],
    ]
    client_table = Table(client_data, colWidths=[1.5*inch, 4.5*inch])
    client_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BACKGROUND', (0, 0), (-1, -1), light_gray),
        ('GRID', (0, 0), (-1, -1), 0.5, medium_gray),
        ('PADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(client_table)
    elements.append(Spacer(1, 10))

    elements.append(Paragraph("TRIP DETAILS:", section_header_style))
    trip_data = [
        [Paragraph(f"<b>Trip Type:</b>", details_content_style), Paragraph(trip_info['trip_type'], details_content_style)],
        [Paragraph(f"<b>Pickup Point:</b>", details_content_style), Paragraph(trip_info['pickup_point'], details_content_style)],
        [Paragraph(f"<b>Drop Off Point:</b>", details_content_style), Paragraph(trip_info['dropoff_point'], details_content_style)],
        [Paragraph(f"<b>Trip Date:</b>", details_content_style), Paragraph(trip_info['trip_date'], details_content_style)],
    ]
    if trip_info['trip_type'] == "Round Trip":
        trip_data.append([Paragraph(f"<b>Return Date:</b>", details_content_style), Paragraph(trip_info['return_date'], details_content_style)])

    trip_table = Table(trip_data, colWidths=[1.5*inch, 4.5*inch])
    trip_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BACKGROUND', (0, 0), (-1, -1), light_gray),
        ('GRID', (0, 0), (-1, -1), 0.5, medium_gray),
        ('PADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(trip_table)
    elements.append(Spacer(1, 10))

    elements.append(Paragraph("SERVICES:", section_header_style))
    currency_symbol = '₦' if has_naira_font else 'N'

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

    services_table = Table(services_data, colWidths=[3.5*inch, 0.7*inch, 0.9*inch, 0.9*inch])
    services_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), primary_blue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), bold_font),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
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
        ('LEFTPADDING', (2, 2), (2, 2), 0),
        ('RIGHTPADDING', (2, 2), (2, 2), 0),
        ('TOPPADDING', (2, 2), (2, 2), 0),
        ('BOTTOMPADDING', (2, 2), (2, 2), 0),
    ]))
    elements.append(services_table)
    elements.append(Spacer(1, 10))

    elements.append(Paragraph("ADDITIONAL NOTES:", section_header_style))
    notes_paragraph = Paragraph(notes, details_content_style)
    notes_table = Table([[notes_paragraph]], colWidths=[6*inch])
    notes_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), light_yellow),
        ('GRID', (0, 0), (-1, -1), 0.5, yellow_border),
        ('PADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(notes_table)
    elements.append(Spacer(1, 10))

    # Signature if available, otherwise use default
    signature_path = signature_path if signature_path and os.path.exists(signature_path) else DEFAULT_SIGNATURE_PATH if os.path.exists(DEFAULT_SIGNATURE_PATH) else None
    if signature_path:
        elements.append(Image(signature_path, width=2*inch, height=0.5*inch))
        elements.append(Spacer(1, 10))

    elements.append(Paragraph(f"<b>Account Details:</b> {company_info['bank_details']}", footer_bank_style))
    elements.append(Paragraph("Thank you for your patronage!", footer_thankyou_style))
    elements.append(Paragraph(f"■ {company_info['tagline']} ■", footer_tagline_style))
    elements.append(Paragraph(company_info['description'], footer_description_style))

    doc.build(elements, onFirstPage=add_page_elements, onLaterPages=add_page_elements)
    return output_path

def generate_receipt_pdf(output_path, receipt_info, client_info, service_info, notes, logo_path=None, signature_path=None):
    doc = SimpleDocTemplate(output_path, pagesize=A4,
                            rightMargin=15, leftMargin=15,
                            topMargin=15, bottomMargin=15)
    elements = []
    styles = getSampleStyleSheet()

    normal_font = naira_font_name
    bold_font = 'Helvetica-Bold' if normal_font == 'Helvetica' else f'{naira_font_name}-Bold'

    primary_blue = HexColor('#3498db')
    light_gray = HexColor('#ecf0f1')
    medium_gray = HexColor('#bdc3c7')
    dark_text = HexColor('#2c3e50')
    light_green = HexColor('#e6ffe6')
    green_border = HexColor('#b3ffb3')

    company_name_style = ParagraphStyle('CompanyNameStyle', parent=styles['Normal'],
                                       fontName=bold_font, fontSize=18, textColor=primary_blue,
                                       alignment=0, spaceAfter=2)
    company_address_style = ParagraphStyle('CompanyAddressStyle', parent=styles['Normal'],
                                           fontName=normal_font, fontSize=8, textColor=dark_text,
                                           alignment=0, spaceAfter=2)
    company_contact_style = ParagraphStyle('CompanyContactStyle', parent=styles['Normal'],
                                           fontName=normal_font, fontSize=8, textColor=dark_text,
                                           alignment=0, spaceAfter=4)

    receipt_title_style = ParagraphStyle('ReceiptTitleStyle', parent=styles['Heading1'],
                                        fontName=bold_font, fontSize=24, textColor=primary_blue,
                                        alignment=1, spaceAfter=20)
    section_header_style = ParagraphStyle('SectionHeaderStyle', parent=styles['Heading2'],
                                          fontName=bold_font, fontSize=10, textColor=colors.white,
                                          backColor=primary_blue, alignment=0, spaceBefore=10,
                                          spaceAfter=5, leftIndent=5, rightIndent=5, borderPadding=3)
    details_content_style = ParagraphStyle('DetailsContentStyle', parent=styles['Normal'],
                                           fontName=normal_font, fontSize=9, textColor=dark_text,
                                           spaceAfter=2)
    amount_paid_label_style = ParagraphStyle('AmountPaidLabelStyle', parent=styles['Normal'],
                                             fontName=bold_font, fontSize=12, textColor=dark_text,
                                             alignment=2)
    amount_paid_value_style = ParagraphStyle('AmountPaidValueStyle', parent=styles['Normal'],
                                             fontName=bold_font, fontSize=12, textColor=primary_blue,
                                             alignment=2)
    footer_bank_style = ParagraphStyle('FooterBankStyle', parent=styles['Normal'],
                                      fontName=bold_font, fontSize=9, textColor=dark_text,
                                      alignment=1, spaceBefore=10, spaceAfter=2)
    footer_thankyou_style = ParagraphStyle('FooterThankYouStyle', parent=styles['Normal'],
                                           fontName=normal_font, fontSize=10, textColor=dark_text,
                                           alignment=1, spaceAfter=2)
    footer_tagline_style = ParagraphStyle('FooterTaglineStyle', parent=styles['Normal'],
                                          fontName=bold_font, fontSize=8, textColor=primary_blue,
                                          alignment=1, spaceAfter=2)
    footer_description_style = ParagraphStyle('FooterDescriptionStyle', parent=styles['Normal'],
                                             fontName=normal_font, fontSize=7, textColor=dark_text,
                                             alignment=1, spaceAfter=10)
    footer_copyright_style = ParagraphStyle('FooterCopyrightStyle', parent=styles['Normal'],
                                            fontName=normal_font, fontSize=6, textColor=colors.grey,
                                            alignment=1, spaceBefore=5)

    def add_page_elements_receipt(canvas_obj, doc):
        add_watermark_hologram(canvas_obj, doc, "NextRide & Logistics")
        canvas_obj.saveState()
        canvas_obj.setFont(normal_font, 6)
        canvas_obj.setFillColor(colors.grey)
        canvas_obj.drawString(doc.leftMargin, 10, company_info['footer'])
        canvas_obj.restoreState()

    # Header with default or uploaded logo on the left
    header_data = []
    logo_path = logo_path if logo_path and os.path.exists(logo_path) else DEFAULT_LOGO_PATH if os.path.exists(DEFAULT_LOGO_PATH) else None
    if logo_path:
        header_data.append([Image(logo_path, width=1.5*inch, height=1.5*inch),
                           Table([[Paragraph(company_info['name'], company_name_style)],
                                  [Paragraph(company_info['address'], company_address_style)],
                                  [Paragraph(f"Phones: {company_info['phones']}", company_contact_style)],
                                  [Paragraph(f"Emails: {company_info['emails']}", company_contact_style)]],
                                 colWidths=[4.5*inch], style=TableStyle([
                                     ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                     ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                                 ]))])
    else:
        header_data.append([Table([[Paragraph(company_info['name'], company_name_style)],
                                  [Paragraph(company_info['address'], company_address_style)],
                                  [Paragraph(f"Phones: {company_info['phones']}", company_contact_style)],
                                  [Paragraph(f"Emails: {company_info['emails']}", company_contact_style)]],
                                 colWidths=[6*inch], style=TableStyle([
                                     ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                     ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                                 ]))])

    header_table = Table(header_data, colWidths=[1.5*inch, 4.5*inch] if logo_path else [6*inch])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))

    elements.append(header_table)
    elements.append(Spacer(1, 10))

    receipt_info_data = [
        [Paragraph("RECEIPT", receipt_title_style)],
        [Paragraph(f"Receipt No: <b>{receipt_info['receipt_number']}</b>", details_content_style)],
        [Paragraph(f"Date: <b>{receipt_info['receipt_date']}</b>", details_content_style)],
    ]
    receipt_info_table = Table(receipt_info_data, colWidths=[6*inch])
    receipt_info_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    elements.append(receipt_info_table)
    elements.append(Spacer(1, 10))

    elements.append(Paragraph("RECEIVED FROM:", section_header_style))
    client_data = [
        [Paragraph(f"<b>Name:</b>", details_content_style), Paragraph(client_info['name'], details_content_style)],
        [Paragraph(f"<b>Address:</b>", details_content_style), Paragraph(client_info['address'], details_content_style)],
        [Paragraph(f"<b>Contact:</b>", details_content_style), Paragraph(client_info['contact'], details_content_style)],
    ]
    client_table = Table(client_data, colWidths=[1.5*inch, 4.5*inch])
    client_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BACKGROUND', (0, 0), (-1, -1), light_gray),
        ('GRID', (0, 0), (-1, -1), 0.5, medium_gray),
        ('PADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(client_table)
    elements.append(Spacer(1, 10))

    elements.append(Paragraph("SERVICE DETAILS:", section_header_style))
    currency_symbol = '₦' if has_naira_font else 'N'

    service_details_data = [
        [Paragraph(f"<b>Description:</b>", details_content_style), Paragraph(service_info['description'], details_content_style)],
        [Paragraph(f"<b>Payment Method:</b>", details_content_style), Paragraph(service_info['payment_method'], details_content_style)],
    ]
    service_details_table = Table(service_details_data, colWidths=[1.5*inch, 4.5*inch])
    service_details_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BACKGROUND', (0, 0), (-1, -1), light_gray),
        ('GRID', (0, 0), (-1, -1), 0.5, medium_gray),
        ('PADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(service_details_table)
    elements.append(Spacer(1, 10))

    amount_summary_data = [
        [Paragraph('<b>AMOUNT PAID:</b>', amount_paid_label_style),
         Paragraph(f'<b>{currency_symbol}{service_info["amount_paid"]:,.2f}</b>', amount_paid_value_style)]
    ]
    amount_summary_table = Table(amount_summary_data, colWidths=[4.5*inch, 1.5*inch])
    amount_summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), light_gray),
        ('GRID', (0, 0), (-1, -1), 0.5, medium_gray),
        ('PADDING', (0, 0), (-1, -1), 5),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(amount_summary_table)
    elements.append(Spacer(1, 10))

    # Signature if available, otherwise use default
    signature_path = signature_path if signature_path and os.path.exists(signature_path) else DEFAULT_SIGNATURE_PATH if os.path.exists(DEFAULT_SIGNATURE_PATH) else None
    if signature_path:
        elements.append(Image(signature_path, width=2*inch, height=0.5*inch))
        elements.append(Spacer(1, 10))

    elements.append(Paragraph("ADDITIONAL NOTES:", section_header_style))
    notes_paragraph = Paragraph(notes, details_content_style)
    notes_table = Table([[notes_paragraph]], colWidths=[6*inch])
    notes_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), light_green),
        ('GRID', (0, 0), (-1, -1), 0.5, green_border),
        ('PADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(notes_table)
    elements.append(Spacer(1, 10))

    elements.append(Paragraph(f"<b>Account Details:</b> {company_info['bank_details']}", footer_bank_style))
    elements.append(Paragraph("Thank you for your payment!", footer_thankyou_style))
    elements.append(Paragraph(f"■ {company_info['tagline']} ■", footer_tagline_style))
    elements.append(Paragraph(company_info['description'], footer_description_style))

    doc.build(elements, onFirstPage=add_page_elements_receipt, onLaterPages=add_page_elements_receipt)
    return output_path

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_invoice', methods=['POST'])
def generate_invoice():
    try:
        # Handle file uploads (optional)
        logo = request.files.get('logo')
        signature = request.files.get('signature')
        logo_path = None
        signature_path = None
        if logo and logo.filename:
            logo_path = os.path.join(app.config['UPLOAD_FOLDER'], logo.filename)
            logo.save(logo_path)
        if signature and signature.filename:
            signature_path = os.path.join(app.config['UPLOAD_FOLDER'], signature.filename)
            signature.save(signature_path)

        client_info = {
            'name': request.form['client_name'],
            'address': request.form['client_address'],
            'contact': request.form['client_contact'],
            'invoice_number': f"INV-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}",
            'invoice_date': datetime.now().strftime('%B %d, %Y')
        }

        trip_info = {
            'trip_type': request.form['trip_type'],
            'pickup_point': request.form['pickup_point'],
            'dropoff_point': request.form['dropoff_point'],
            'trip_date': request.form['trip_date'],
            'return_date': request.form.get('return_date', '')
        }

        service_info = {
            'description': request.form['description'],
            'quantity': int(request.form['quantity']),
            'price': float(request.form['price']),
            'amount': int(request.form['quantity']) * float(request.form['price'])
        }

        notes = request.form['notes']

        filename = f"Invoice_{client_info['invoice_number']}.pdf"
        generate_invoice_pdf(filename, client_info, trip_info, service_info, notes, logo_path, signature_path)

        # Clean up uploaded files if used
        if logo_path and os.path.exists(logo_path):
            os.remove(logo_path)
        if signature_path and os.path.exists(signature_path):
            os.remove(signature_path)

        return send_file(filename, as_attachment=True)

    except Exception as e:
        return f"Error generating invoice: {str(e)}", 400

@app.route('/generate_receipt', methods=['POST'])
def generate_receipt():
    try:
        # Handle file uploads (optional)
        logo = request.files.get('logo')
        signature = request.files.get('signature')
        logo_path = None
        signature_path = None
        if logo and logo.filename:
            logo_path = os.path.join(app.config['UPLOAD_FOLDER'], logo.filename)
            logo.save(logo_path)
        if signature and signature.filename:
            signature_path = os.path.join(app.config['UPLOAD_FOLDER'], signature.filename)
            signature.save(signature_path)

        client_info = {
            'name': request.form['client_name'],
            'address': request.form['client_address'],
            'contact': request.form['client_contact']
        }

        receipt_info = {
            'receipt_number': f"REC-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}",
            'receipt_date': datetime.now().strftime('%B %d, %Y')
        }

        service_info = {
            'description': request.form['description'],
            'amount_paid': float(request.form['amount_paid']),
            'payment_method': request.form['payment_method']
        }

        notes = request.form['notes']

        filename = f"Receipt_{receipt_info['receipt_number']}.pdf"
        generate_receipt_pdf(filename, receipt_info, client_info, service_info, notes, logo_path, signature_path)

        # Clean up uploaded files if used
        if logo_path and os.path.exists(logo_path):
            os.remove(logo_path)
        if signature_path and os.path.exists(signature_path):
            os.remove(signature_path)

        return send_file(filename, as_attachment=True)

    except Exception as e:
        return f"Error generating receipt: {str(e)}", 400

if __name__ == '__main__':
    app.run(debug=True)