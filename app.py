from flask import Flask, render_template, request, send_file, jsonify
import os
import random
import tempfile
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, ListFlowable, ListItem, \
    KeepTogether
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus.flowables import Spacer, HRFlowable
import traceback

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['STATIC_FOLDER'] = 'static'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create necessary directories
for folder in [app.config['UPLOAD_FOLDER'], app.config['STATIC_FOLDER']]:
    if not os.path.exists(folder):
        os.makedirs(folder)
        print(f"Created directory: {folder}")

# Default logo and signature paths - ABSOLUTE PATHS
DEFAULT_LOGO_PATH = os.path.join(app.config['STATIC_FOLDER'], 'logo.png')
DEFAULT_SIGNATURE_PATH = os.path.join(app.config['STATIC_FOLDER'], 'signature.png')


# Create placeholder images if they don't exist
def create_placeholder_image(path, width=200, height=100, color=(200, 200, 200), text="Placeholder"):
    """Create a placeholder image if the default image doesn't exist"""
    if not os.path.exists(path):
        try:
            from PIL import Image as PILImage, ImageDraw, ImageFont
            img = PILImage.new('RGB', (width, height), color)
            draw = ImageDraw.Draw(img)

            # Try to use a font
            try:
                # Try different font paths
                font_paths = [
                    "arial.ttf",
                    "Arial.ttf",
                    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
                    "C:/Windows/Fonts/arial.ttf"
                ]
                font = None
                for font_path in font_paths:
                    try:
                        font = ImageFont.truetype(font_path, 20)
                        break
                    except:
                        continue

                if font is None:
                    font = ImageFont.load_default()

            except:
                font = ImageFont.load_default()

            # Calculate text position (center)
            text_width = draw.textlength(text, font=font) if hasattr(draw, 'textlength') else len(text) * 10
            text_height = 20
            text_position = ((width - text_width) // 2, (height - text_height) // 2)

            draw.text(text_position, text, fill=(100, 100, 100), font=font)
            img.save(path)
            print(f"Created placeholder image: {path}")
        except ImportError:
            print(f"PIL not installed, cannot create placeholder image at {path}")
        except Exception as e:
            print(f"Error creating placeholder image: {e}")


# Create placeholders for default images
create_placeholder_image(DEFAULT_LOGO_PATH, 200, 100, (230, 240, 250), "NEXT RIDE LOGO")
create_placeholder_image(DEFAULT_SIGNATURE_PATH, 200, 50, (250, 230, 230), "SIGNATURE")

# Initialize company info with improved formatting
company_info = {
    'name': 'NextRide & Logistics',
    'address': 'No 29 Amoda Alli Street, Millennium Estate, Gbagada, Lagos, Nigeria',
    'phones': '08023428564, 08128859763',
    'emails': 'nextflight77@gmail.com, janeagboola@yahoo.com',
    'tagline': 'Safety. Luxury. Value for Your Money.',
    'description': 'Our vehicles are well-maintained with fully functional AC for maximum comfort. We offer rentals—daily, weekly, or monthly—backed by professional and courteous drivers. Enjoy interstate travel with peace of mind, knowing you\'re in safe hands.',
    'footer': 'Copyright © 2025 | Invoice powered by Opygoal Technology Ltd. | Developer: Oladotun Ajakaiye, Service Manager & Data Analyst',
    'bank_details': 'Bank: Sterling Bank | Account No: 0123186628 | Name: NextRide & Logistics'
}

# Brand colors from LaTeX example
BRAND_BLUE = HexColor('#003399')  # RGB(0, 51, 153)
LIGHT_GREY = HexColor('#f5f5f5')  # RGB(245, 245, 245)
LIGHT_BLUE = HexColor('#e6f2ff')  # Lighter blue for backgrounds

# FONT CONFIGURATION
UNIVERSAL_FONT_NAME = 'Helvetica'
UNIVERSAL_BOLD_FONT_NAME = 'Helvetica-Bold'
# Use "N" instead of Naira symbol to avoid encoding issues
currency_symbol = 'N'  # Using "N" for Naira instead of ₦


# Define improved styles based on LaTeX layout
def get_styles():
    """Get consistent styles for both invoice and receipt with improved layout"""
    styles = getSampleStyleSheet()

    # Override all default styles to use our universal font
    for style_name in styles.byName:
        style = styles[style_name]
        style.fontName = UNIVERSAL_FONT_NAME
        if 'Heading' in style_name or 'Title' in style_name:
            style.fontName = UNIVERSAL_BOLD_FONT_NAME

    # BASE STYLE
    base_style = ParagraphStyle('UniversalBaseStyle', parent=styles['Normal'],
                                fontName=UNIVERSAL_FONT_NAME,
                                fontSize=9,
                                textColor=colors.black,
                                alignment=TA_LEFT,
                                spaceAfter=1,
                                leading=11)

    # COMPANY NAME - Large brand blue like LaTeX example
    company_name_style = ParagraphStyle('CompanyNameStyle', parent=base_style,
                                        fontName=UNIVERSAL_BOLD_FONT_NAME,
                                        fontSize=28,
                                        textColor=BRAND_BLUE,
                                        leading=30,
                                        spaceAfter=2)

    # TAGLINE STYLE - Italic
    tagline_style = ParagraphStyle('TaglineStyle', parent=base_style,
                                   fontSize=10,
                                   textColor=colors.black,
                                   spaceAfter=2,
                                   leading=12)

    # COMPANY ADDRESS - Right aligned like LaTeX
    company_address_style = ParagraphStyle('CompanyAddressStyle', parent=base_style,
                                           fontSize=9,
                                           alignment=TA_RIGHT,
                                           leading=11,
                                           spaceAfter=1)

    # INVOICE TITLE - Large brand blue
    invoice_title_style = ParagraphStyle('InvoiceTitleStyle', parent=base_style,
                                         fontName=UNIVERSAL_BOLD_FONT_NAME,
                                         fontSize=24,
                                         textColor=BRAND_BLUE,
                                         alignment=TA_LEFT,
                                         spaceAfter=6,
                                         leading=26)

    # RECEIPT TITLE
    receipt_title_style = ParagraphStyle('ReceiptTitleStyle', parent=base_style,
                                         fontName=UNIVERSAL_BOLD_FONT_NAME,
                                         fontSize=24,
                                         textColor=BRAND_BLUE,
                                         alignment=TA_LEFT,
                                         spaceAfter=6,
                                         leading=26)

    # SECTION HEADERS
    section_header_style = ParagraphStyle('SectionHeaderStyle', parent=base_style,
                                          fontName=UNIVERSAL_BOLD_FONT_NAME,
                                          fontSize=10,
                                          textColor=colors.black,
                                          alignment=TA_LEFT,
                                          spaceBefore=8,
                                          spaceAfter=4,
                                          leading=12)

    # DETAILS CONTENT
    details_content_style = ParagraphStyle('DetailsContentStyle', parent=base_style,
                                           fontSize=9,
                                           spaceAfter=2,
                                           leading=11)

    # BOLD DETAILS CONTENT
    bold_details_style = ParagraphStyle('BoldDetailsStyle', parent=details_content_style,
                                        fontName=UNIVERSAL_BOLD_FONT_NAME)

    # CENTERED CONTENT STYLE (for signature text)
    centered_content_style = ParagraphStyle('CenteredContentStyle', parent=base_style,
                                            fontSize=9,
                                            alignment=TA_CENTER,
                                            spaceAfter=2,
                                            leading=11)

    # BOLD CENTERED STYLE
    bold_centered_style = ParagraphStyle('BoldCenteredStyle', parent=centered_content_style,
                                         fontName=UNIVERSAL_BOLD_FONT_NAME)

    # SERVICE TITLE STYLE (for main service description)
    service_title_style = ParagraphStyle('ServiceTitleStyle', parent=base_style,
                                         fontName=UNIVERSAL_BOLD_FONT_NAME,
                                         fontSize=10,
                                         spaceAfter=4,
                                         leading=12)

    # SERVICE DESCRIPTION STYLE
    service_desc_style = ParagraphStyle('ServiceDescStyle', parent=base_style,
                                        fontSize=9,
                                        spaceAfter=4,
                                        leading=11)

    # ITALIC ROUTE STYLE
    route_style = ParagraphStyle('RouteStyle', parent=base_style,
                                 fontSize=9,
                                 textColor=colors.darkgrey,
                                 spaceAfter=4,
                                 leading=11)

    # SERVICE SCOPE HEADER
    scope_header_style = ParagraphStyle('ScopeHeaderStyle', parent=base_style,
                                        fontName=UNIVERSAL_BOLD_FONT_NAME,
                                        fontSize=9,
                                        spaceAfter=2,
                                        leading=11)

    # BULLET LIST STYLE (for service scope items)
    bullet_style = ParagraphStyle('BulletStyle', parent=base_style,
                                  fontSize=8,
                                  leftIndent=10,
                                  spaceBefore=1,
                                  spaceAfter=1,
                                  leading=10,
                                  bulletIndent=5)

    # TABLE HEADER STYLE
    table_header_style = ParagraphStyle('TableHeaderStyle', parent=base_style,
                                        fontName=UNIVERSAL_BOLD_FONT_NAME,
                                        fontSize=10,
                                        textColor=colors.white,
                                        alignment=TA_CENTER,
                                        leading=12)

    # TABLE CELL STYLE
    table_cell_style = ParagraphStyle('TableCellStyle', parent=base_style,
                                      fontSize=9,
                                      alignment=TA_LEFT,
                                      leading=11)

    # TABLE CELL CENTERED (for Qty, Price, Amount)
    table_cell_center_style = ParagraphStyle('TableCellCenterStyle', parent=table_cell_style,
                                             alignment=TA_CENTER)

    # TABLE CELL RIGHT ALIGNED (for amounts)
    table_cell_right_style = ParagraphStyle('TableCellRightStyle', parent=table_cell_style,
                                            alignment=TA_RIGHT)

    # TOTAL STYLES
    total_label_style = ParagraphStyle('TotalLabelStyle', parent=base_style,
                                       fontName=UNIVERSAL_BOLD_FONT_NAME,
                                       fontSize=10,
                                       alignment=TA_RIGHT,
                                       leading=12)

    total_amount_style = ParagraphStyle('TotalAmountStyle', parent=base_style,
                                        fontName=UNIVERSAL_BOLD_FONT_NAME,
                                        fontSize=10,
                                        textColor=BRAND_BLUE,
                                        alignment=TA_RIGHT,
                                        leading=12)

    # AMOUNT PAID STYLE FOR RECEIPT
    amount_paid_style = ParagraphStyle('AmountPaidStyle', parent=base_style,
                                       fontName=UNIVERSAL_BOLD_FONT_NAME,
                                       fontSize=14,
                                       textColor=BRAND_BLUE,
                                       alignment=TA_CENTER,
                                       spaceBefore=12,
                                       spaceAfter=12,
                                       leading=16)

    # FOOTER STYLES
    footer_style = ParagraphStyle('FooterStyle', parent=base_style,
                                  fontSize=8,
                                  alignment=TA_LEFT,
                                  spaceBefore=12,
                                  leading=10)

    footer_right_style = ParagraphStyle('FooterRightStyle', parent=footer_style,
                                        alignment=TA_RIGHT)

    footer_text_style = ParagraphStyle('FooterTextStyle', parent=base_style,
                                       fontSize=7,
                                       alignment=TA_CENTER,
                                       textColor=colors.grey,
                                       leading=9)

    notes_style = ParagraphStyle('NotesStyle', parent=base_style,
                                 fontSize=8,
                                 alignment=TA_JUSTIFY,
                                 leading=10)

    return {
        'styles': styles,
        'colors': {
            'brand_blue': BRAND_BLUE,
            'light_grey': LIGHT_GREY,
            'light_blue': LIGHT_BLUE,
            'medium_gray': HexColor('#dee2e6'),
            'yellow_border': HexColor('#ffe6b3'),
            'light_yellow': HexColor('#fff9e6'),
            'light_green': HexColor('#e6ffe6'),
            'green_border': HexColor('#b3ffb3')
        },
        'paragraph_styles': {
            'base': base_style,
            'company_name': company_name_style,
            'tagline': tagline_style,
            'company_address': company_address_style,
            'invoice_title': invoice_title_style,
            'receipt_title': receipt_title_style,
            'section_header': section_header_style,
            'details_content': details_content_style,
            'bold_details': bold_details_style,
            'centered_content': centered_content_style,
            'bold_centered': bold_centered_style,
            'service_title': service_title_style,
            'service_desc': service_desc_style,
            'route': route_style,
            'scope_header': scope_header_style,
            'bullet': bullet_style,
            'table_header': table_header_style,
            'table_cell': table_cell_style,
            'table_cell_center': table_cell_center_style,
            'table_cell_right': table_cell_right_style,
            'total_label': total_label_style,
            'total_amount': total_amount_style,
            'amount_paid': amount_paid_style,
            'footer': footer_style,
            'footer_right': footer_right_style,
            'footer_text': footer_text_style,
            'notes': notes_style
        }
    }


def create_bullet_list(items, bullet_style):
    """Create a bullet list from items"""
    bullet_list = []
    for item in items:
        bullet_list.append(ListItem(Paragraph(item, bullet_style), leftIndent=10))
    return ListFlowable(bullet_list, bulletType='bullet', leftIndent=20)


def parse_service_scope(scope_text):
    """Parse service scope text into bullet points"""
    if not scope_text:
        return []

    # Split by common bullet point indicators
    lines = scope_text.split('\n')
    items = []

    for line in lines:
        line = line.strip()
        if line:
            # Remove bullet characters if present
            line = line.lstrip('•-*◦‣⁃⁌⁍⦁⦾⦿')
            line = line.strip()
            if line:
                items.append(line)

    return items


def format_service_description(description, route=None, service_scope=None):
    """Format service description with proper structure like LaTeX example"""
    elements = []

    if description:
        # Split into title and description
        lines = description.split('\n')
        if lines:
            # First line as title
            elements.append(Paragraph(lines[0], get_styles()['paragraph_styles']['service_title']))

            # Rest as description
            if len(lines) > 1:
                desc_text = ' '.join(lines[1:])
                elements.append(Paragraph(desc_text, get_styles()['paragraph_styles']['service_desc']))

    if route:
        # Use <i> tags for italic effect
        elements.append(Paragraph(f"<i>Route: {route}</i>", get_styles()['paragraph_styles']['route']))

    if service_scope:
        scope_items = parse_service_scope(service_scope)
        if scope_items:
            elements.append(Paragraph("<b>Service Scope Includes:</b>",
                                      get_styles()['paragraph_styles']['scope_header']))
            elements.append(create_bullet_list(scope_items, get_styles()['paragraph_styles']['bullet']))

    return elements


def add_watermark_hologram(canvas_obj, doc):
    """Add watermark/hologram to the document - MORE VISIBLE VERSION"""
    try:
        canvas_obj.saveState()
        # Use brand blue with more visibility
        canvas_obj.setFillColor(BRAND_BLUE)
        canvas_obj.setStrokeColor(BRAND_BLUE)

        # Set larger font and more visible alpha
        canvas_obj.setFont(UNIVERSAL_BOLD_FONT_NAME, 48)  # Larger font
        canvas_obj.setFillAlpha(0.08)  # More visible
        canvas_obj.setStrokeAlpha(0.08)

        # Rotated text across the entire page
        text = "NEXT RIDE & LOGISTICS"
        for x in range(-100, int(doc.pagesize[0]) + 100, 250):
            for y in range(-100, int(doc.pagesize[1]) + 100, 180):
                canvas_obj.saveState()
                canvas_obj.translate(x, y)
                canvas_obj.rotate(30)  # 30 degree angle
                canvas_obj.drawCentredString(0, 0, text)
                canvas_obj.restoreState()

        # Add a second layer with smaller text at different angle
        canvas_obj.setFont(UNIVERSAL_FONT_NAME, 32)
        canvas_obj.setFillAlpha(0.05)
        for x in range(-50, int(doc.pagesize[0]) + 50, 200):
            for y in range(-50, int(doc.pagesize[1]) + 50, 150):
                canvas_obj.saveState()
                canvas_obj.translate(x, y)
                canvas_obj.rotate(-15)  # Opposite angle
                canvas_obj.drawCentredString(0, 0, "CONFIDENTIAL")
                canvas_obj.restoreState()

        canvas_obj.restoreState()
    except Exception as e:
        print(f"Warning: Could not add watermark: {e}")


def add_footer(canvas_obj, doc):
    """Add footer to all pages - using universal font"""
    try:
        canvas_obj.saveState()
        canvas_obj.setFont(UNIVERSAL_FONT_NAME, 7)
        canvas_obj.setFillColor(colors.grey)
        footer_text = company_info['footer']
        canvas_obj.drawCentredString(doc.pagesize[0] / 2, 12, footer_text)
        canvas_obj.restoreState()
    except Exception as e:
        print(f"Warning: Could not add footer: {e}")


def safe_image_loader(image_path, width=None, height=None):
    """Safely load an image for ReportLab with error handling"""
    try:
        if image_path and os.path.exists(image_path):
            print(f"Loading image from: {image_path}")
            # Use ImageReader to handle different image formats
            img_reader = ImageReader(image_path)

            # Get original dimensions
            img_width, img_height = img_reader.getSize()

            # Calculate aspect ratio
            aspect = img_height / float(img_width)

            # Set default width if not provided
            if width is None:
                width = min(img_width, 200)  # Max 200 points width

            # Calculate height maintaining aspect ratio
            if height is None:
                height = width * aspect
            else:
                # If both width and height provided, maintain aspect ratio
                new_height = width * aspect
                if new_height > height:
                    width = height / aspect
                else:
                    height = new_height

            print(f"Image loaded: {image_path}, size: {width}x{height}")

            # Create Image object
            img = Image(image_path, width=width, height=height)
            return img
        else:
            print(f"Image path does not exist: {image_path}")
            return None
    except Exception as e:
        print(f"Error loading image {image_path}: {e}")
        # Try to create a placeholder
        try:
            print(f"Creating placeholder for missing image: {image_path}")
            placeholder = Image(DEFAULT_LOGO_PATH if 'logo' in str(image_path).lower() else DEFAULT_SIGNATURE_PATH,
                                width=width or 100, height=height or 50)
            return placeholder
        except:
            return None


def generate_invoice_pdf(output_path, client_info, trip_info, service_info, notes, logo_path=None, signature_path=None):
    """Generate invoice PDF with improved LaTeX-like layout"""
    try:
        if not output_path:
            output_path = tempfile.mktemp(suffix='.pdf')

        doc = SimpleDocTemplate(output_path, pagesize=A4,
                                rightMargin=0.5 * inch,
                                leftMargin=0.5 * inch,
                                topMargin=0.5 * inch,
                                bottomMargin=0.75 * inch)
        elements = []

        # Get styles
        style_config = get_styles()
        colors_dict = style_config['colors']
        para_styles = style_config['paragraph_styles']

        def add_page_elements(canvas_obj, doc):
            """Add watermark and footer to each page"""
            try:
                add_watermark_hologram(canvas_obj, doc)
                add_footer(canvas_obj, doc)
            except Exception as e:
                print(f"Warning in page elements: {e}")

        # HEADER SECTION - Improved like LaTeX with LOGO
        header_data = []

        # Try to load logo
        logo_img = safe_image_loader(logo_path or DEFAULT_LOGO_PATH, width=1.5 * inch, height=0.8 * inch)

        if logo_img:
            # Left side: Logo
            logo_cell = [logo_img]
        else:
            # If no logo, use text placeholder
            logo_cell = [Paragraph("NEXT RIDE", para_styles['company_name'])]

        # Right side: Company info
        right_content = [
            Paragraph("<b>NextRide & Logistics</b>", para_styles['company_address']),
            Paragraph(company_info['address'], para_styles['company_address']),
            Paragraph(f"Tel: {company_info['phones']}", para_styles['company_address']),
            Paragraph(f"Email: {company_info['emails']}", para_styles['company_address'])
        ]

        # Create two-column header with logo
        header_table = Table([[logo_cell, right_content]],
                             colWidths=[2.0 * inch, 3.5 * inch])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ]))

        elements.append(header_table)
        elements.append(Spacer(1, 5))

        # Tagline under header
        elements.append(Paragraph(f"<i>{company_info['tagline']}</i>", para_styles['tagline']))
        elements.append(Spacer(1, 8))

        # INVOICE TITLE with horizontal rule
        elements.append(Paragraph("INVOICE", para_styles['invoice_title']))

        # Add horizontal rule like LaTeX
        hr = HRFlowable(width="100%", thickness=1, color=BRAND_BLUE,
                        spaceBefore=2, spaceAfter=10)
        elements.append(hr)

        elements.append(Spacer(1, 8))

        # INVOICE INFO & BILL TO - Two columns like LaTeX
        invoice_details_data = [
            [
                # Left column: BILL TO
                [
                    Paragraph("<b>BILL TO:</b>", para_styles['section_header']),
                    Paragraph(f"<b>{client_info['name']}</b>", para_styles['details_content']),
                    Paragraph(client_info['address'], para_styles['details_content']),
                    Paragraph(f"Tel: {client_info['contact']}", para_styles['details_content'])
                ],
                # Right column: INVOICE DETAILS
                [
                    Paragraph("<b>INVOICE DETAILS:</b>", para_styles['section_header']),
                    Paragraph(f"Invoice No: {client_info['invoice_number']}", para_styles['details_content']),
                    Paragraph(f"Date: {client_info['invoice_date']}", para_styles['details_content']),
                    Paragraph(f"Trip Date: {trip_info['trip_date']}", para_styles['details_content']),
                    Paragraph(f"Trip Type: {trip_info['trip_type']}", para_styles['details_content'])
                ]
            ]
        ]

        invoice_details_table = Table(invoice_details_data, colWidths=[2.75 * inch, 2.75 * inch])
        invoice_details_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ]))

        elements.append(invoice_details_table)
        elements.append(Spacer(1, 20))

        # SERVICES TABLE - Improved layout like LaTeX
        elements.append(Spacer(1, 5))

        # Table data
        services_data = []

        # Header row
        services_data.append([
            Paragraph('Description', para_styles['table_header']),
            Paragraph('Qty', para_styles['table_header']),
            Paragraph(f'Price ({currency_symbol})', para_styles['table_header']),
            Paragraph(f'Total ({currency_symbol})', para_styles['table_header'])
        ])

        # Service row - with formatted description
        description_elements = format_service_description(
            service_info['description'],
            service_info.get('route', ''),
            service_info.get('service_scope', '')
        )

        # Create a table cell with multiple elements
        description_cell = []
        for element in description_elements:
            description_cell.append(element)

        services_data.append([
            description_cell,
            Paragraph(str(service_info['quantity']), para_styles['table_cell_center']),
            Paragraph(f"{service_info['price']:,.2f}", para_styles['table_cell_right']),
            Paragraph(f"{service_info['amount']:,.2f}", para_styles['table_cell_right'])
        ])

        # Total row
        services_data.append([
            '',
            '',
            Paragraph('<b>TOTAL AMOUNT:</b>', para_styles['total_label']),
            Paragraph(f'<b>{currency_symbol}{service_info["amount"]:,.2f}</b>', para_styles['total_amount'])
        ])

        # Create table with adjusted column widths
        services_table = Table(services_data, colWidths=[3.5 * inch, 0.5 * inch, 1.0 * inch, 1.0 * inch])

        # Apply styles
        services_table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), colors_dict['brand_blue']),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), UNIVERSAL_BOLD_FONT_NAME),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 6),

            # Service row
            ('BACKGROUND', (0, 1), (-1, 1), colors.white),
            ('VALIGN', (0, 1), (-1, 1), 'TOP'),
            ('LEFTPADDING', (0, 1), (0, 1), 8),
            ('RIGHTPADDING', (0, 1), (0, 1), 8),
            ('TOPPADDING', (0, 1), (0, 1), 8),
            ('BOTTOMPADDING', (0, 1), (0, 1), 8),

            # Grid lines
            ('LINEABOVE', (0, 0), (-1, 0), 1, colors.white),
            ('LINEBELOW', (0, 0), (-1, 0), 1, colors.white),
            ('LINEBELOW', (0, 1), (-1, 1), 0.5, colors.lightgrey),

            # Total row
            ('SPAN', (0, 2), (1, 2)),
            ('BACKGROUND', (2, 2), (-1, 2), colors_dict['light_grey']),
            ('ALIGN', (2, 2), (-1, 2), 'RIGHT'),
            ('FONTNAME', (2, 2), (-1, 2), UNIVERSAL_BOLD_FONT_NAME),
            ('TOPPADDING', (2, 2), (-1, 2), 8),
            ('BOTTOMPADDING', (2, 2), (-1, 2), 8),
            ('LINEABOVE', (2, 2), (-1, 2), 1, colors.grey),
        ]))

        elements.append(services_table)
        elements.append(Spacer(1, 25))

        # SIGNATURE SECTION - CENTERED
        elements.append(Spacer(1, 10))

        # Create a centered table for signature and text
        signature_data = []

        # Try to load signature
        signature_img = safe_image_loader(signature_path or DEFAULT_SIGNATURE_PATH, width=2.0 * inch, height=0.6 * inch)

        if signature_img:
            # Create a centered cell with signature image
            signature_cell = Table([[signature_img]], colWidths=[4.5 * inch])
            signature_cell.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ]))
            signature_data.append([signature_cell])

        # Add centered text under signature
        signature_text = Table([
            [Paragraph("Authorized Signature", para_styles['centered_content'])],
            [Paragraph("NextRide & Logistics", para_styles['bold_centered'])]
        ], colWidths=[4.5 * inch])

        signature_text.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))

        signature_data.append([signature_text])

        # Combine everything in one centered table
        signature_table = Table(signature_data, colWidths=[4.5 * inch])
        signature_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))

        elements.append(signature_table)
        elements.append(Spacer(1, 20))

        # FOOTER SECTION - Two columns like LaTeX
        footer_data = [
            [
                # Left column: Account Details
                [
                    Paragraph("<b>ACCOUNT DETAILS:</b>", para_styles['footer']),
                    Paragraph(company_info['bank_details'], para_styles['details_content'])
                ],
                # Right column: Notes
                [
                    Paragraph("<b>Notes:</b>", para_styles['footer_right']),
                    Paragraph(notes if notes else "Payment is due within 7 days. Thank you for choosing NextRide!",
                              para_styles['notes'])
                ]
            ]
        ]

        footer_table = Table(footer_data, colWidths=[2.75 * inch, 2.75 * inch])
        footer_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ]))

        elements.append(footer_table)
        elements.append(Spacer(1, 15))

        # Build the document
        doc.build(elements, onFirstPage=add_page_elements, onLaterPages=add_page_elements)
        print(f"Successfully generated invoice PDF: {output_path}")
        return output_path

    except Exception as e:
        print(f"Error generating invoice PDF: {e}")
        print(traceback.format_exc())
        raise


def generate_receipt_pdf(output_path, receipt_info, client_info, service_info, notes, logo_path=None,
                         signature_path=None):
    """Generate receipt PDF with improved LaTeX-like layout"""
    try:
        if not output_path:
            output_path = tempfile.mktemp(suffix='.pdf')

        doc = SimpleDocTemplate(output_path, pagesize=A4,
                                rightMargin=0.5 * inch,
                                leftMargin=0.5 * inch,
                                topMargin=0.5 * inch,
                                bottomMargin=0.75 * inch)
        elements = []

        # Get styles
        style_config = get_styles()
        colors_dict = style_config['colors']
        para_styles = style_config['paragraph_styles']

        def add_page_elements_receipt(canvas_obj, doc):
            try:
                add_watermark_hologram(canvas_obj, doc)
                add_footer(canvas_obj, doc)
            except Exception as e:
                print(f"Warning in receipt page elements: {e}")

        # HEADER SECTION - Same as invoice with LOGO
        header_data = []

        # Try to load logo
        logo_img = safe_image_loader(logo_path or DEFAULT_LOGO_PATH, width=1.5 * inch, height=0.8 * inch)

        if logo_img:
            # Left side: Logo
            logo_cell = [logo_img]
        else:
            # If no logo, use text placeholder
            logo_cell = [Paragraph("NEXT RIDE", para_styles['company_name'])]

        # Right side: Company info
        right_content = [
            Paragraph("<b>NextRide & Logistics</b>", para_styles['company_address']),
            Paragraph(company_info['address'], para_styles['company_address']),
            Paragraph(f"Tel: {company_info['phones']}", para_styles['company_address']),
            Paragraph(f"Email: {company_info['emails']}", para_styles['company_address'])
        ]

        # Create two-column header with logo
        header_table = Table([[logo_cell, right_content]],
                             colWidths=[2.0 * inch, 3.5 * inch])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ]))

        elements.append(header_table)
        elements.append(Spacer(1, 5))

        # Tagline under header
        elements.append(Paragraph(f"<i>{company_info['tagline']}</i>", para_styles['tagline']))
        elements.append(Spacer(1, 8))

        # RECEIPT TITLE with horizontal rule
        elements.append(Paragraph("RECEIPT", para_styles['receipt_title']))

        # Add horizontal rule
        hr = HRFlowable(width="100%", thickness=1, color=BRAND_BLUE,
                        spaceBefore=2, spaceAfter=10)
        elements.append(hr)

        elements.append(Spacer(1, 8))

        # RECEIPT INFO & RECEIVED FROM - Two columns
        receipt_details_data = [
            [
                # Left column: RECEIVED FROM
                [
                    Paragraph("<b>RECEIVED FROM:</b>", para_styles['section_header']),
                    Paragraph(f"<b>{client_info['name']}</b>", para_styles['details_content']),
                    Paragraph(client_info['address'], para_styles['details_content']),
                    Paragraph(f"Tel: {client_info['contact']}", para_styles['details_content'])
                ],
                # Right column: RECEIPT DETAILS
                [
                    Paragraph("<b>RECEIPT DETAILS:</b>", para_styles['section_header']),
                    Paragraph(f"Receipt No: {receipt_info['receipt_number']}", para_styles['details_content']),
                    Paragraph(f"Date: {receipt_info['receipt_date']}", para_styles['details_content']),
                    Paragraph(f"Payment Method: {service_info['payment_method']}", para_styles['details_content'])
                ]
            ]
        ]

        receipt_details_table = Table(receipt_details_data, colWidths=[2.75 * inch, 2.75 * inch])
        receipt_details_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ]))

        elements.append(receipt_details_table)
        elements.append(Spacer(1, 20))

        # AMOUNT PAID SECTION
        elements.append(Spacer(1, 10))
        elements.append(Paragraph(f"<b>AMOUNT RECEIVED:</b>", para_styles['section_header']))
        elements.append(Spacer(1, 5))

        # Create a box for the amount
        amount_box = Table([[Paragraph(f"{currency_symbol}{service_info['amount_paid']:,.2f}",
                                       para_styles['amount_paid'])]],
                           colWidths=[4.5 * inch])
        amount_box.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), LIGHT_BLUE),
            ('BOX', (0, 0), (-1, -1), 1, BRAND_BLUE),
            ('PADDING', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        elements.append(amount_box)
        elements.append(Spacer(1, 15))

        # SERVICE DESCRIPTION
        elements.append(Paragraph("<b>SERVICE DESCRIPTION:</b>", para_styles['section_header']))
        elements.append(Spacer(1, 5))

        description_elements = format_service_description(
            service_info['description'],
            service_info.get('route', ''),
            service_info.get('service_scope', '')
        )

        for element in description_elements:
            elements.append(element)

        elements.append(Spacer(1, 20))

        # SIGNATURE SECTION - CENTERED
        elements.append(Spacer(1, 10))

        # Create a centered table for signature and text
        signature_data = []

        # Try to load signature
        signature_img = safe_image_loader(signature_path or DEFAULT_SIGNATURE_PATH, width=2.0 * inch, height=0.6 * inch)

        if signature_img:
            # Create a centered cell with signature image
            signature_cell = Table([[signature_img]], colWidths=[4.5 * inch])
            signature_cell.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ]))
            signature_data.append([signature_cell])

        # Add centered text under signature
        signature_text = Table([
            [Paragraph("Authorized Signature", para_styles['centered_content'])],
            [Paragraph("NextRide & Logistics", para_styles['bold_centered'])]
        ], colWidths=[4.5 * inch])

        signature_text.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))

        signature_data.append([signature_text])

        # Combine everything in one centered table
        signature_table = Table(signature_data, colWidths=[4.5 * inch])
        signature_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))

        elements.append(signature_table)
        elements.append(Spacer(1, 20))

        # FOOTER SECTION
        footer_data = [
            [
                # Left column: Account Details
                [
                    Paragraph("<b>ACCOUNT DETAILS:</b>", para_styles['footer']),
                    Paragraph(company_info['bank_details'], para_styles['details_content'])
                ],
                # Right column: Notes
                [
                    Paragraph("<b>Notes:</b>", para_styles['footer_right']),
                    Paragraph(notes if notes else "Thank you for your payment!",
                              para_styles['notes'])
                ]
            ]
        ]

        footer_table = Table(footer_data, colWidths=[2.75 * inch, 2.75 * inch])
        footer_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ]))

        elements.append(footer_table)
        elements.append(Spacer(1, 15))

        # Build the document
        doc.build(elements, onFirstPage=add_page_elements_receipt, onLaterPages=add_page_elements_receipt)
        print(f"Successfully generated receipt PDF: {output_path}")
        return output_path

    except Exception as e:
        print(f"Error generating receipt PDF: {e}")
        print(traceback.format_exc())
        raise


# Flask Routes

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/update_company_info', methods=['POST'])
def update_company_info():
    """Update company information via API"""
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400

        # Update company_info dictionary
        for key, value in data.items():
            if key in company_info:
                company_info[key] = value

        print(f"Updated company info: {company_info}")
        return jsonify({'success': True, 'message': 'Company information updated successfully'})

    except Exception as e:
        print(f"Error updating company info: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/get_company_info', methods=['GET'])
def get_company_info():
    """Get current company information"""
    try:
        return jsonify(company_info)
    except Exception as e:
        print(f"Error getting company info: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/generate_invoice', methods=['POST'])
def generate_invoice_route():
    try:
        # Handle file uploads
        logo = request.files.get('logo')
        signature = request.files.get('signature')
        logo_path = None
        signature_path = None

        if logo and logo.filename:
            logo_filename = f"logo_{random.randint(1000, 9999)}_{logo.filename}"
            logo_path = os.path.join(app.config['UPLOAD_FOLDER'], logo_filename)
            logo.save(logo_path)
            print(f"Saved logo to: {logo_path}")

        if signature and signature.filename:
            signature_filename = f"signature_{random.randint(1000, 9999)}_{signature.filename}"
            signature_path = os.path.join(app.config['UPLOAD_FOLDER'], signature_filename)
            signature.save(signature_path)
            print(f"Saved signature to: {signature_path}")

        # Collect form data
        client_info = {
            'name': request.form.get('client_name', 'Not Provided'),
            'address': request.form.get('client_address', 'Not Provided'),
            'contact': request.form.get('client_contact', 'Not Provided'),
            'invoice_number': f"INV-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}",
            'invoice_date': datetime.now().strftime('%B %d, %Y')
        }

        trip_info = {
            'trip_type': request.form.get('trip_type', 'One Way'),
            'pickup_point': request.form.get('pickup_point', 'Not Provided'),
            'dropoff_point': request.form.get('dropoff_point', 'Not Provided'),
            'trip_date': request.form.get('trip_date', datetime.now().strftime('%Y-%m-%d')),
            'return_date': request.form.get('return_date', '')
        }

        try:
            quantity = int(request.form.get('quantity', 1))
            price = float(request.form.get('price', 0))
            amount = quantity * price
        except:
            quantity = 1
            price = 0
            amount = 0

        # Get enhanced service description fields
        description = request.form.get('description', 'Transportation Service')
        route = request.form.get('route', '')
        service_scope = request.form.get('service_scope', '')

        service_info = {
            'description': description,
            'route': route,
            'service_scope': service_scope,
            'quantity': quantity,
            'price': price,
            'amount': amount
        }

        notes = request.form.get('notes', '')

        filename = f"Invoice_{client_info['invoice_number']}.pdf"
        print(f"Generating invoice: {filename}")

        # Generate PDF
        pdf_path = generate_invoice_pdf(filename, client_info, trip_info, service_info, notes, logo_path,
                                        signature_path)

        # Clean up uploaded files
        if logo_path and os.path.exists(logo_path):
            try:
                os.remove(logo_path)
            except:
                pass

        if signature_path and os.path.exists(signature_path):
            try:
                os.remove(signature_path)
            except:
                pass

        # Send file
        return send_file(pdf_path,
                         as_attachment=True,
                         download_name=filename,
                         mimetype='application/pdf')

    except Exception as e:
        error_msg = f"Error generating invoice: {str(e)}"
        print(error_msg)
        print(traceback.format_exc())
        return jsonify({'error': error_msg}), 500


@app.route('/generate_receipt', methods=['POST'])
def generate_receipt_route():
    try:
        # Handle file uploads
        logo = request.files.get('logo')
        signature = request.files.get('signature')
        logo_path = None
        signature_path = None

        if logo and logo.filename:
            logo_filename = f"logo_{random.randint(1000, 9999)}_{logo.filename}"
            logo_path = os.path.join(app.config['UPLOAD_FOLDER'], logo_filename)
            logo.save(logo_path)
            print(f"Saved logo to: {logo_path}")

        if signature and signature.filename:
            signature_filename = f"signature_{random.randint(1000, 9999)}_{signature.filename}"
            signature_path = os.path.join(app.config['UPLOAD_FOLDER'], signature_filename)
            signature.save(signature_path)
            print(f"Saved signature to: {signature_path}")

        # Collect form data
        client_info = {
            'name': request.form.get('client_name', 'Not Provided'),
            'address': request.form.get('client_address', 'Not Provided'),
            'contact': request.form.get('client_contact', 'Not Provided')
        }

        receipt_info = {
            'receipt_number': f"REC-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}",
            'receipt_date': datetime.now().strftime('%B %d, %Y')
        }

        try:
            amount_paid = float(request.form.get('amount_paid', 0))
        except:
            amount_paid = 0

        # Get enhanced service description fields
        description = request.form.get('description', 'Transportation Service')
        route = request.form.get('route', '')
        service_scope = request.form.get('service_scope', '')

        service_info = {
            'description': description,
            'route': route,
            'service_scope': service_scope,
            'amount_paid': amount_paid,
            'payment_method': request.form.get('payment_method', 'Cash')
        }

        notes = request.form.get('notes', '')

        filename = f"Receipt_{receipt_info['receipt_number']}.pdf"
        print(f"Generating receipt: {filename}")

        # Generate PDF
        pdf_path = generate_receipt_pdf(filename, receipt_info, client_info, service_info, notes, logo_path,
                                        signature_path)

        # Clean up uploaded files
        if logo_path and os.path.exists(logo_path):
            try:
                os.remove(logo_path)
            except:
                pass

        if signature_path and os.path.exists(signature_path):
            try:
                os.remove(signature_path)
            except:
                pass

        # Send file
        return send_file(pdf_path,
                         as_attachment=True,
                         download_name=filename,
                         mimetype='application/pdf')

    except Exception as e:
        error_msg = f"Error generating receipt: {str(e)}"
        print(error_msg)
        print(traceback.format_exc())
        return jsonify({'error': error_msg}), 500


@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy', 'message': 'PDF Generator is running'})


if __name__ == '__main__':
    # Check for required dependencies
    try:
        import reportlab

        print(f"ReportLab version: {reportlab.__version__}")
    except ImportError:
        print("ERROR: ReportLab is not installed. Run: pip install reportlab")

    try:
        from PIL import Image as PILImage

        print("PIL/Pillow is available for image processing")
    except ImportError:
        print("WARNING: PIL/Pillow is not installed. Run: pip install Pillow")

    print(f"Starting server...")
    print(f"Static folder: {app.config['STATIC_FOLDER']}")
    print(f"Upload folder: {app.config['UPLOAD_FOLDER']}")
    print(f"Default logo path: {DEFAULT_LOGO_PATH}")
    print(f"Default signature path: {DEFAULT_SIGNATURE_PATH}")
    print(f"Using universal font: {UNIVERSAL_FONT_NAME} throughout all documents")
    print(f"Brand color: {BRAND_BLUE}")
    print(f"Currency symbol: '{currency_symbol}' (N for Naira)")

    # Verify static files exist
    print(f"Logo file exists: {os.path.exists(DEFAULT_LOGO_PATH)}")
    print(f"Signature file exists: {os.path.exists(DEFAULT_SIGNATURE_PATH)}")

    # Create better placeholder images if they don't exist
    if not os.path.exists(DEFAULT_LOGO_PATH):
        create_placeholder_image(DEFAULT_LOGO_PATH, 400, 200, (230, 240, 250), "NEXT RIDE\nLOGO")
    if not os.path.exists(DEFAULT_SIGNATURE_PATH):
        create_placeholder_image(DEFAULT_SIGNATURE_PATH, 300, 100, (250, 230, 230), "AUTHORIZED\nSIGNATURE")

    app.run(debug=True, host='0.0.0.0', port=5000)