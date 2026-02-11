from flask import Flask, render_template, request, send_file, jsonify
import os
import random
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.utils import ImageReader
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.units import inch, mm
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import Color, gray
import io
import base64
import json

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize company info - ALL PLACEHOLDERS REMOVED
company_info = {
    'name': '',
    'address': '',
    'phones': '',
    'emails': '',
    'tagline': '',
    'description': '',
    'footer': '',
    'bank_details': ''
}

# Font setup - Using Courier New for monospaced alignment
try:
    # Try to register Courier New font for perfect column alignment
    courier_font_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cour.ttf')
    courier_bold_font_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'courbd.ttf')

    if os.path.exists(courier_font_path):
        pdfmetrics.registerFont(TTFont('CourierNew', courier_font_path))
        normal_font = 'CourierNew'
        print("INFO: Successfully registered Courier New font")
    else:
        # Fallback to Courier which is standard monospaced font in PDF
        normal_font = 'Courier'
        print("WARNING: Courier New font not found. Using standard Courier.")

    if os.path.exists(courier_bold_font_path):
        pdfmetrics.registerFont(TTFont('CourierNew-Bold', courier_bold_font_path))
        bold_font = 'CourierNew-Bold'
        print("INFO: Successfully registered Courier New Bold font")
    else:
        bold_font = 'Courier-Bold'
        print("WARNING: Courier New Bold font not found. Using standard Courier-Bold.")

    # Register standard fonts as fallback
    pdfmetrics.registerFont(TTFont('Courier', 'Courier'))
    pdfmetrics.registerFont(TTFont('Courier-Bold', 'Courier-Bold'))

except Exception as e:
    print(f"ERROR: Could not register Courier fonts ({e}). Using standard Courier.")
    normal_font = 'Courier'
    bold_font = 'Courier-Bold'

# Global font sizes for consistent monospaced layout
MONOSPACED_FONT_SIZE = 9
MONOSPACED_SMALL_SIZE = 8
MONOSPACED_HEADER_SIZE = 10
MONOSPACED_TITLE_SIZE = 12


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/get_company_info', methods=['GET'])
def get_company_info():
    """Return current company information"""
    return jsonify(company_info)


@app.route('/update_company_info', methods=['POST'])
def update_company_info():
    """Update company information from the UI"""
    global company_info
    try:
        data = request.get_json()
        if data:
            company_info.update({
                'name': data.get('name', ''),
                'address': data.get('address', ''),
                'phones': data.get('phones', ''),
                'emails': data.get('emails', ''),
                'tagline': data.get('tagline', ''),
                'description': data.get('description', ''),
                'footer': data.get('footer', ''),
                'bank_details': data.get('bank_details', '')
            })
            return jsonify({'success': True, 'message': 'Company information updated successfully'})
        return jsonify({'success': False, 'message': 'No data received'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error updating company info: {str(e)}'})


def add_watermark_hologram(canvas_obj, doc, text_to_watermark):
    """Add watermark hologram to PDF pages"""
    canvas_obj.saveState()
    canvas_obj.setFillColor(Color(0.2, 0.6, 0.8, alpha=0.15))
    canvas_obj.setStrokeColor(Color(0.2, 0.6, 0.8, alpha=0.15))

    for x in range(0, int(doc.pagesize[0]), 120):
        for y in range(0, int(doc.pagesize[1]), 100):
            canvas_obj.saveState()
            canvas_obj.translate(x, y)
            canvas_obj.rotate(45)
            canvas_obj.setFont(bold_font, 20)
            canvas_obj.setFillAlpha(0.1)
            canvas_obj.drawString(0, 0, text_to_watermark)
            canvas_obj.restoreState()

    canvas_obj.restoreState()


def format_currency(value):
    """Format currency with proper spacing for monospaced font"""
    return f"NGN {value:,.2f}"


def create_monospaced_table(data, col_widths, style=None):
    """Create a table with monospaced font styling"""
    if style is None:
        style = TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), normal_font),
            ('FONTSIZE', (0, 0), (-1, -1), MONOSPACED_FONT_SIZE),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ])
    return Table(data, colWidths=col_widths), style


def format_text_for_monospace(text, max_length=None):
    """Format text to work well with monospaced font"""
    if not text:
        return ""

    # Replace multiple spaces with single spaces for better alignment
    text = ' '.join(text.split())

    if max_length and len(text) > max_length:
        # Simple word wrap for monospace
        words = text.split()
        lines = []
        current_line = []
        current_length = 0

        for word in words:
            if current_length + len(word) + 1 <= max_length:
                current_line.append(word)
                current_length += len(word) + 1
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
                current_length = len(word)

        if current_line:
            lines.append(' '.join(current_line))

        return '<br/>'.join(lines)

    return text


def debug_multiple_trips_data(multiple_trips):
    """Debug function to print multiple trips data"""
    print(f"=== DEBUG MULTIPLE TRIPS DATA ===")
    print(f"Number of trips: {len(multiple_trips)}")
    for i, trip in enumerate(multiple_trips, 1):
        print(f"Trip {i}:")
        print(f"  Pickup: {trip.get('pickup', 'N/A')}")
        print(f"  Destination: {trip.get('destination', 'N/A')}")
        print(f"  Dropoff: {trip.get('dropoff', 'N/A')}")
        print(f"  Trip Date: {trip.get('tripDate', 'N/A')}")
        print(f"  Trip Time: {trip.get('tripTime', 'N/A')}")
        print(f"  Return Date: {trip.get('returnDate', 'N/A')}")
        print(f"  Return Time: {trip.get('returnTime', 'N/A')}")
        print(f"  Price: {trip.get('price', 'N/A')}")
    print("=== END DEBUG ===")


def validate_trip_data(trip_type, pickup_point, dropoff_point, trip_date, multiple_trips):
    """Validate trip data based on trip type"""
    if trip_type == "Multiple Round Trips":
        if not multiple_trips:
            return False, "Please add at least one trip for Multiple Round Trips"

        # Validate each trip in multiple trips
        for i, trip in enumerate(multiple_trips, 1):
            if not trip.get('pickup') or not trip.get('destination') or not trip.get('tripDate'):
                return False, f"Trip {i} is missing required fields (Pickup, Destination, or Trip Date)"

            try:
                price = float(trip.get('price', 0))
                if price <= 0:
                    return False, f"Trip {i} must have a valid price greater than 0"
            except (ValueError, TypeError):
                return False, f"Trip {i} has an invalid price format"

    else:  # Single Trip or Round Trip
        if not pickup_point or not dropoff_point or not trip_date:
            return False, "Please fill in all required trip details"

        if trip_type == "Round Trip" and not trip.get('returnDate', ''):
            return False, "Return Date is required for Round Trips"

    return True, "Validation successful"


@app.route('/generate_invoice', methods=['POST'])
def generate_invoice():
    try:
        print("Starting invoice generation...")

        # Get form data with proper defaults
        client_name = request.form.get('client_name', '').strip()
        client_address = request.form.get('client_address', '').strip()
        client_contact = request.form.get('client_contact', '').strip()
        trip_type = request.form.get('trip_type', 'Single Trip')
        pickup_point = request.form.get('pickup_point', '').strip()
        dropoff_point = request.form.get('dropoff_point', '').strip()
        trip_date = request.form.get('trip_date', '').strip()
        trip_time = request.form.get('trip_time', '').strip()
        return_date = request.form.get('return_date', '').strip()
        return_time = request.form.get('return_time', '').strip()
        invoice_number = request.form.get('invoice_number', '').strip()
        invoice_date = request.form.get('invoice_date', '').strip()
        description = request.form.get('description', '').strip()

        # Handle numeric fields with proper validation
        try:
            quantity = int(request.form.get('quantity', 1))
        except (ValueError, TypeError):
            quantity = 1

        try:
            price = float(request.form.get('price', 0))
        except (ValueError, TypeError):
            price = 0.0

        notes = request.form.get('notes', '').strip()

        # Handle multiple trips data - FIXED: Proper JSON parsing
        multiple_trips_data = request.form.get('multiple_trips', '[]')
        print(f"Multiple trips data received: {multiple_trips_data}")

        try:
            multiple_trips = json.loads(multiple_trips_data)
            # Debug the parsed data
            debug_multiple_trips_data(multiple_trips)
        except json.JSONDecodeError as e:
            print(f"Error parsing multiple trips data: {e}")
            multiple_trips = []
        except Exception as e:
            print(f"Unexpected error parsing trips data: {e}")
            multiple_trips = []

        print(f"Parsed {len(multiple_trips)} multiple trips")

        # Handle file uploads
        logo_file = request.files.get('logo')
        signature_file = request.files.get('signature')

        logo_path = None
        signature_path = None

        if logo_file and logo_file.filename:
            try:
                logo_filename = f"logo_{datetime.now().strftime('%Y%m%d%H%M%S')}_{logo_file.filename}"
                logo_path = os.path.join(app.config['UPLOAD_FOLDER'], logo_filename)
                logo_file.save(logo_path)
                print(f"Logo saved to: {logo_path}")
            except Exception as e:
                print(f"Error saving logo: {e}")

        if signature_file and signature_file.filename:
            try:
                signature_filename = f"signature_{datetime.now().strftime('%Y%m%d%H%M%S')}_{signature_file.filename}"
                signature_path = os.path.join(app.config['UPLOAD_FOLDER'], signature_filename)
                signature_file.save(signature_path)
                print(f"Signature saved to: {signature_path}")
            except Exception as e:
                print(f"Error saving signature: {e}")

        # Validate required fields
        required_fields = {
            'client_name': client_name,
            'client_address': client_address,
            'invoice_number': invoice_number,
            'invoice_date': invoice_date
        }

        missing_fields = [field for field, value in required_fields.items() if not value]
        if missing_fields:
            error_msg = f"Missing required fields: {', '.join(missing_fields)}"
            print(f"Validation error: {error_msg}")
            return jsonify({'error': error_msg}), 400

        # Validate trip-specific fields
        is_valid, validation_msg = validate_trip_data(trip_type, pickup_point, dropoff_point, trip_date, multiple_trips)
        if not is_valid:
            print(f"Validation error: {validation_msg}")
            return jsonify({'error': validation_msg}), 400

        # Create PDF in memory
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=15 * mm,
            leftMargin=15 * mm,
            topMargin=15 * mm,
            bottomMargin=15 * mm
        )

        elements = []
        styles = getSampleStyleSheet()

        # Define colors
        primary_blue = HexColor('#2c3e50')
        secondary_blue = HexColor('#3498db')
        light_gray = HexColor('#f8f9fa')
        medium_gray = HexColor('#e9ecef')
        dark_gray = HexColor('#495057')
        accent_color = HexColor('#e74c3c')

        # Monospaced Font Styles - FIXED: Consistent font usage
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            fontName=bold_font,
            fontSize=MONOSPACED_TITLE_SIZE,
            textColor=primary_blue,
            alignment=1,
            spaceAfter=12
        )

        header_style = ParagraphStyle(
            'HeaderStyle',
            parent=styles['Heading2'],
            fontName=bold_font,
            fontSize=MONOSPACED_HEADER_SIZE,
            textColor=colors.white,
            backColor=primary_blue,
            alignment=0,
            spaceBefore=8,
            spaceAfter=6,
            leftIndent=8,
            borderPadding=5
        )

        company_header_style = ParagraphStyle(
            'CompanyHeaderStyle',
            parent=styles['Normal'],
            fontName=bold_font,
            fontSize=MONOSPACED_TITLE_SIZE,
            textColor=primary_blue,
            alignment=1,
            spaceAfter=4
        )

        company_subheader_style = ParagraphStyle(
            'CompanySubheaderStyle',
            parent=styles['Normal'],
            fontName=normal_font,
            fontSize=MONOSPACED_SMALL_SIZE,
            textColor=dark_gray,
            alignment=1,
            spaceAfter=2
        )

        label_style = ParagraphStyle(
            'LabelStyle',
            parent=styles['Normal'],
            fontName=bold_font,
            fontSize=MONOSPACED_FONT_SIZE,
            textColor=dark_gray,
            alignment=0,
            spaceAfter=2
        )

        value_style = ParagraphStyle(
            'ValueStyle',
            parent=styles['Normal'],
            fontName=normal_font,
            fontSize=MONOSPACED_FONT_SIZE,
            textColor=colors.black,
            alignment=0,
            spaceAfter=2
        )

        table_header_style = ParagraphStyle(
            'TableHeaderStyle',
            parent=styles['Normal'],
            fontName=bold_font,
            fontSize=MONOSPACED_FONT_SIZE,
            textColor=colors.white,
            alignment=1
        )

        table_cell_style = ParagraphStyle(
            'TableCellStyle',
            parent=styles['Normal'],
            fontName=normal_font,
            fontSize=MONOSPACED_SMALL_SIZE,
            textColor=colors.black,
            alignment=0
        )

        table_cell_center_style = ParagraphStyle(
            'TableCellCenterStyle',
            parent=styles['Normal'],
            fontName=normal_font,
            fontSize=MONOSPACED_SMALL_SIZE,
            textColor=colors.black,
            alignment=1
        )

        table_cell_right_style = ParagraphStyle(
            'TableCellRightStyle',
            parent=styles['Normal'],
            fontName=normal_font,
            fontSize=MONOSPACED_SMALL_SIZE,
            textColor=colors.black,
            alignment=2
        )

        # FIXED: Total style now uses same font size and family
        total_style = ParagraphStyle(
            'TotalStyle',
            parent=styles['Normal'],
            fontName=bold_font,
            fontSize=MONOSPACED_SMALL_SIZE,  # Same size as other table cells
            textColor=primary_blue,
            alignment=2
        )

        footer_style = ParagraphStyle(
            'FooterStyle',
            parent=styles['Normal'],
            fontName=normal_font,
            fontSize=MONOSPACED_SMALL_SIZE,
            textColor=dark_gray,
            alignment=1,
            spaceBefore=5
        )

        def add_page_elements(canvas_obj, doc):
            watermark_text = company_info['name'] if company_info['name'] else "INVOICE"
            add_watermark_hologram(canvas_obj, doc, watermark_text)
            canvas_obj.saveState()
            canvas_obj.setFont(normal_font, 6)
            canvas_obj.setFillColor(colors.grey)
            footer_text = company_info.get('footer', '')
            canvas_obj.drawString(doc.leftMargin, 10, footer_text)
            canvas_obj.restoreState()

        # 1. Header Section with Monospaced Layout
        header_data = []

        # Company Info - Only show if provided
        if company_info['name']:
            company_lines = []
            company_lines.append([Paragraph(company_info['name'], company_header_style)])

            if company_info['address']:
                company_lines.append([Paragraph(company_info['address'], company_subheader_style)])

            if company_info['phones']:
                company_lines.append([Paragraph(f"Phones: {company_info['phones']}", company_subheader_style)])

            if company_info['emails']:
                company_lines.append([Paragraph(f"Emails: {company_info['emails']}", company_subheader_style)])

            if company_lines:
                company_info_table = Table(company_lines, colWidths=[6 * inch])
                company_info_table.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (-1, -1), normal_font),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ]))
                elements.append(company_info_table)
                elements.append(Spacer(1, 15))

        # Invoice Title and Details
        invoice_header_table = Table([
            [Paragraph("TAX INVOICE", title_style)],
            [Paragraph(f"Invoice Number: {invoice_number}", value_style)],
            [Paragraph(f"Invoice Date: {invoice_date}", value_style)]
        ], colWidths=[6 * inch])

        invoice_header_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), normal_font),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('BACKGROUND', (0, 0), (-1, 0), medium_gray),
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ('PADDING', (0, 0), (-1, -1), 8),
        ]))

        elements.append(invoice_header_table)
        elements.append(Spacer(1, 15))

        # 2. Client Information Section
        elements.append(Paragraph("CLIENT INFORMATION", header_style))

        client_data = [
            [Paragraph("Name:", label_style), Paragraph(format_text_for_monospace(client_name, 50), value_style)],
            [Paragraph("Address:", label_style), Paragraph(format_text_for_monospace(client_address, 50), value_style)],
            [Paragraph("Contact:", label_style), Paragraph(format_text_for_monospace(client_contact, 50), value_style)]
        ]

        client_table = Table(client_data, colWidths=[1.2 * inch, 4.8 * inch])
        client_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), normal_font),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.5, medium_gray),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('BACKGROUND', (0, 0), (0, -1), light_gray),
        ]))

        elements.append(client_table)
        elements.append(Spacer(1, 12))

        # 3. Trip Details Section - FIXED: Multiple Round Trips data display
        elements.append(Paragraph("TRIP DETAILS", header_style))

        if trip_type == "Multiple Round Trips" and multiple_trips:
            # Enhanced Multiple Trips Display with Monospaced Alignment
            trip_summary_data = [
                [Paragraph("Trip Type:", label_style),
                 Paragraph(f"Multiple Round Trips - {len(multiple_trips)} Scheduled Trips", value_style)]
            ]

            trip_summary_table = Table(trip_summary_data, colWidths=[1.2 * inch, 4.8 * inch])
            trip_summary_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), normal_font),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('GRID', (0, 0), (-1, -1), 0.5, medium_gray),
                ('PADDING', (0, 0), (-1, -1), 6),
                ('BACKGROUND', (0, 0), (0, -1), light_gray),
            ]))
            elements.append(trip_summary_table)
            elements.append(Spacer(1, 8))

            # Detailed Trips Table - FIXED: Proper data extraction from multiple_trips
            trips_header = [
                Paragraph('Trip #', table_header_style),
                Paragraph('Pickup Point', table_header_style),
                Paragraph('Destination', table_header_style),
                Paragraph('Drop Off Point', table_header_style),
                Paragraph('Trip Date/Time', table_header_style),
                Paragraph('Return Date/Time', table_header_style),
                Paragraph('Amount', table_header_style)
            ]

            trips_data = [trips_header]
            total_amount = 0

            for i, trip in enumerate(multiple_trips, 1):
                # FIXED: Extract all trip data properly
                pickup = trip.get('pickup', 'N/A')
                destination = trip.get('destination', 'N/A')
                dropoff = trip.get('dropoff', 'N/A')
                trip_date_val = trip.get('tripDate', 'N/A')
                trip_time_val = trip.get('tripTime', 'N/A')
                return_date_val = trip.get('returnDate', 'N/A')
                return_time_val = trip.get('returnTime', 'N/A')

                # Format dates and times
                departure_info = f"{trip_date_val}\n{trip_time_val}" if trip_date_val != 'N/A' else 'N/A'
                return_info = f"{return_date_val}\n{return_time_val}" if return_date_val != 'N/A' else 'N/A'

                trip_price = float(trip.get('price', 0))
                total_amount += trip_price

                trips_data.append([
                    Paragraph(str(i), table_cell_center_style),
                    Paragraph(format_text_for_monospace(pickup, 20), table_cell_style),
                    Paragraph(format_text_for_monospace(destination, 20), table_cell_style),
                    Paragraph(format_text_for_monospace(dropoff, 20), table_cell_style),
                    Paragraph(departure_info, table_cell_style),
                    Paragraph(return_info, table_cell_style),
                    Paragraph(f"NGN {trip_price:,.2f}", table_cell_right_style)
                ])

            # Add total row with perfect alignment and consistent font
            trips_data.append([
                Paragraph('', table_cell_style),
                Paragraph('', table_cell_style),
                Paragraph('', table_cell_style),
                Paragraph('', table_cell_style),
                Paragraph('', table_cell_style),
                Paragraph('<b>TOTAL:</b>', table_header_style),
                Paragraph(f'<b>NGN {total_amount:,.2f}</b>', total_style)  # Using consistent font style
            ])

            trips_table = Table(trips_data,
                                colWidths=[0.4 * inch, 1.0 * inch, 1.0 * inch, 1.0 * inch, 1.0 * inch, 1.0 * inch,
                                           0.6 * inch])
            trips_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), normal_font),  # Consistent font throughout
                ('BACKGROUND', (0, 0), (-1, 0), primary_blue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), bold_font),
                ('FONTSIZE', (0, 0), (-1, 0), MONOSPACED_FONT_SIZE),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -2), light_gray),
                ('GRID', (0, 0), (-1, -1), 0.5, medium_gray),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('PADDING', (0, 0), (-1, -1), 5),
                ('BACKGROUND', (0, -1), (-1, -1), medium_gray),
                ('FONTNAME', (0, -1), (-1, -1), bold_font),
                ('FONTSIZE', (0, -1), (-1, -1), MONOSPACED_SMALL_SIZE),  # Consistent font size
                ('ALIGN', (-1, 0), (-1, -1), 'RIGHT'),  # Right align amount column
            ]))

            elements.append(trips_table)

        else:
            # Single/Round Trip Display - MONOSPACED
            trip_data = [
                [Paragraph("Trip Type:", label_style), Paragraph(trip_type, value_style)],
                [Paragraph("Pickup Point:", label_style),
                 Paragraph(format_text_for_monospace(pickup_point, 50), value_style)],
                [Paragraph("Drop Off Point:", label_style),
                 Paragraph(format_text_for_monospace(dropoff_point, 50), value_style)],
                [Paragraph("Trip Date:", label_style), Paragraph(trip_date, value_style)],
                [Paragraph("Trip Time:", label_style), Paragraph(trip_time, value_style)],
            ]

            if trip_type == "Round Trip":
                trip_data.extend([
                    [Paragraph("Return Date:", label_style), Paragraph(return_date, value_style)],
                    [Paragraph("Return Time:", label_style), Paragraph(return_time, value_style)]
                ])

            trip_table = Table(trip_data, colWidths=[1.2 * inch, 4.8 * inch])
            trip_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), normal_font),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('GRID', (0, 0), (-1, -1), 0.5, medium_gray),
                ('PADDING', (0, 0), (-1, -1), 6),
                ('BACKGROUND', (0, 0), (0, -1), light_gray),
            ]))
            elements.append(trip_table)

        elements.append(Spacer(1, 15))

        # 4. Services and Pricing Section - FIXED: Consistent font in totals
        elements.append(Paragraph("SERVICES & PAYMENT SUMMARY", header_style))

        if trip_type == "Multiple Round Trips" and multiple_trips:
            # Summary for multiple trips with perfect monospaced alignment
            total_amount = sum(float(trip.get('price', 0)) for trip in multiple_trips)
            avg_price = total_amount / len(multiple_trips) if multiple_trips else 0

            services_data = [
                [Paragraph('Description', table_header_style),
                 Paragraph('Qty', table_header_style),
                 Paragraph('Unit Price', table_header_style),
                 Paragraph('Amount', table_header_style)],
                [Paragraph(format_text_for_monospace(description, 35), table_cell_style),
                 Paragraph(str(len(multiple_trips)), table_cell_center_style),
                 Paragraph(f"NGN {avg_price:,.2f}", table_cell_right_style),
                 Paragraph(f"NGN {total_amount:,.2f}", table_cell_right_style)],
                ['', '', Paragraph('<b>GRAND TOTAL:</b>', table_header_style),
                 Paragraph(f'<b>NGN {total_amount:,.2f}</b>', total_style)]  # Using consistent font style
            ]

            services_table = Table(services_data, colWidths=[3.0 * inch, 0.6 * inch, 1.2 * inch, 1.2 * inch])
        else:
            # Single/Round trip with monospaced alignment
            qty = quantity
            price_val = price
            amount = qty * price_val
            if trip_type == "Round Trip":
                amount = amount * 2

            services_data = [
                [Paragraph('Description', table_header_style),
                 Paragraph('Qty', table_header_style),
                 Paragraph('Unit Price', table_header_style),
                 Paragraph('Amount', table_header_style)],
                [Paragraph(format_text_for_monospace(description, 35), table_cell_style),
                 Paragraph(str(qty), table_cell_center_style),
                 Paragraph(f"NGN {price_val:,.2f}", table_cell_right_style),
                 Paragraph(f"NGN {amount:,.2f}", table_cell_right_style)],
                ['', '', Paragraph('<b>GRAND TOTAL:</b>', table_header_style),
                 Paragraph(f'<b>NGN {amount:,.2f}</b>', total_style)]  # Using consistent font style
            ]

            services_table = Table(services_data, colWidths=[3.0 * inch, 0.6 * inch, 1.2 * inch, 1.2 * inch])

        services_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), normal_font),  # Consistent font throughout
            ('BACKGROUND', (0, 0), (-1, 0), primary_blue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), bold_font),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, 1), light_gray),
            ('GRID', (0, 0), (-1, -1), 0.5, medium_gray),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('BACKGROUND', (0, 2), (-1, 2), medium_gray),
            ('FONTNAME', (0, 2), (-1, 2), bold_font),
            ('FONTSIZE', (0, 2), (-1, 2), MONOSPACED_SMALL_SIZE),  # Consistent font size
            ('ALIGN', (2, 0), (3, -1), 'RIGHT'),  # Right align price columns
        ]))
        elements.append(services_table)
        elements.append(Spacer(1, 15))

        # 5. Additional Notes Section
        if notes:
            elements.append(Paragraph("ADDITIONAL NOTES", header_style))
            notes_table = Table([[Paragraph(format_text_for_monospace(notes, 70), value_style)]], colWidths=[6 * inch])
            notes_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), normal_font),
                ('BACKGROUND', (0, 0), (-1, -1), light_gray),
                ('GRID', (0, 0), (-1, -1), 0.5, medium_gray),
                ('PADDING', (0, 0), (-1, -1), 8),
            ]))
            elements.append(notes_table)
            elements.append(Spacer(1, 12))

        # 6. Footer Section
        footer_data = []

        if company_info['bank_details']:
            footer_data.append([Paragraph(f"Bank Account Details: {company_info['bank_details']}", value_style)])

        footer_data.extend([
            [Paragraph("Thank you for your business! We appreciate your patronage.", value_style)],
        ])

        if company_info['tagline']:
            footer_data.append([Paragraph(f"{company_info['tagline']}", label_style)])

        if company_info['description']:
            footer_data.append([Paragraph(company_info['description'], footer_style)])

        if footer_data:
            footer_table = Table(footer_data, colWidths=[6 * inch])
            footer_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), normal_font),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('PADDING', (0, 0), (-1, -1), 6),
            ]))
            elements.append(footer_table)

        # Signature Section
        if signature_path and os.path.exists(signature_path):
            try:
                elements.append(Spacer(1, 10))
                signature = Image(signature_path, width=1.5 * inch, height=0.75 * inch)
                signature_table = Table([[signature]], colWidths=[6 * inch])
                signature_table.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (-1, -1), normal_font),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER')
                ]))
                elements.append(signature_table)
                elements.append(Paragraph("Authorized Signature", footer_style))
            except Exception as e:
                print(f"Error adding signature: {e}")

        # Build PDF
        print("Building PDF...")
        doc.build(elements, onFirstPage=add_page_elements, onLaterPages=add_page_elements)
        print("PDF built successfully")

        # Prepare response
        buffer.seek(0)

        # Clean up uploaded files
        if logo_path and os.path.exists(logo_path):
            try:
                os.remove(logo_path)
            except Exception as e:
                print(f"Error removing logo file: {e}")

        if signature_path and os.path.exists(signature_path):
            try:
                os.remove(signature_path)
            except Exception as e:
                print(f"Error removing signature file: {e}")

        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"{invoice_number}.pdf",
            mimetype='application/pdf'
        )

    except Exception as e:
        print(f"Error generating invoice: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to generate invoice: {str(e)}'}), 500


@app.route('/generate_receipt', methods=['POST'])
def generate_receipt():
    """Generate receipt PDF - simplified version of invoice"""
    try:
        # Get form data
        client_name = request.form.get('client_name', '').strip()
        client_contact = request.form.get('client_contact', '').strip()
        amount_paid = request.form.get('amount_paid', '0').strip()
        payment_date = request.form.get('payment_date', '').strip()
        payment_method = request.form.get('payment_method', '').strip()
        receipt_number = request.form.get('receipt_number', '').strip()
        description = request.form.get('description', '').strip()

        # Validate required fields
        if not all([client_name, amount_paid, payment_date, receipt_number]):
            return jsonify({'error': 'Missing required fields for receipt'}), 400

        # Create PDF in memory
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=15 * mm,
            leftMargin=15 * mm,
            topMargin=15 * mm,
            bottomMargin=15 * mm
        )

        elements = []
        styles = getSampleStyleSheet()

        # Create styles for receipt
        title_style = ParagraphStyle(
            'ReceiptTitleStyle',
            parent=styles['Heading1'],
            fontName=bold_font,
            fontSize=14,
            textColor=HexColor('#2c3e50'),
            alignment=1,
            spaceAfter=12
        )

        header_style = ParagraphStyle(
            'ReceiptHeaderStyle',
            parent=styles['Heading2'],
            fontName=bold_font,
            fontSize=10,
            textColor=colors.white,
            backColor=HexColor('#2c3e50'),
            alignment=0,
            spaceBefore=8,
            spaceAfter=6,
            leftIndent=8
        )

        # Add company info if available
        if company_info['name']:
            elements.append(Paragraph(company_info['name'], title_style))
        elements.append(Paragraph("OFFICIAL RECEIPT", title_style))
        elements.append(Spacer(1, 12))

        # Receipt details
        receipt_data = [
            [Paragraph("Receipt Number:", header_style), Paragraph(receipt_number, value_style)],
            [Paragraph("Payment Date:", header_style), Paragraph(payment_date, value_style)],
            [Paragraph("Client Name:", header_style), Paragraph(client_name, value_style)],
            [Paragraph("Contact:", header_style), Paragraph(client_contact, value_style)],
            [Paragraph("Amount Paid:", header_style), Paragraph(f"NGN {float(amount_paid):,.2f}", value_style)],
            [Paragraph("Payment Method:", header_style), Paragraph(payment_method, value_style)],
            [Paragraph("Description:", header_style), Paragraph(description, value_style)]
        ]

        receipt_table = Table(receipt_data, colWidths=[2 * inch, 4 * inch])
        receipt_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), normal_font),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#e9ecef')),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('BACKGROUND', (0, 0), (0, -1), HexColor('#f8f9fa')),
        ]))

        elements.append(receipt_table)
        elements.append(Spacer(1, 20))

        # Footer
        footer_text = "Payment Received. Thank You!"
        elements.append(Paragraph(footer_text, title_style))

        # Build PDF
        doc.build(elements)
        buffer.seek(0)

        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"{receipt_number}_receipt.pdf",
            mimetype='application/pdf'
        )

    except Exception as e:
        print(f"Error generating receipt: {e}")
        return jsonify({'error': f'Failed to generate receipt: {str(e)}'}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)