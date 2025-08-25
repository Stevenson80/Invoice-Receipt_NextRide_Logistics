import sys
import os
import random
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QTabWidget, QLineEdit, QTextEdit, QLabel, QPushButton,
                             QGroupBox, QFormLayout, QSpinBox, QDoubleSpinBox, QComboBox,
                             QFileDialog, QMessageBox, QDateEdit, QGridLayout, QScrollArea)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QPixmap
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
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.colors import Color, gray
import math


class NextRideApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NextRide & Logistics - Invoice and Receipt Generator")
        self.setGeometry(100, 100, 1000, 800)

        # Initialize company info with updated address
        self.company_info = {
            'name': 'NextRide & Logistics',
            'address': 'No 29 Amoda Alli Street, Millennium Estate, Gbagada, Lagos. Nigeria',
            'phones': '08023428564 or 08128859763',
            'emails': 'nextflight77@gmail.com, janeagboola@yahoo.com',
            'tagline': 'Safety. Luxury. Value for Your Money.',
            'description': 'Our vehicles are well-maintained with fully functional AC for maximum comfort. We offer rentals—daily, weekly, or monthly—backed by professional and courteous drivers. Enjoy interstate travel with peace of mind, knowing you\'re in safe hands.',
            'footer': 'Copyright © 2025 | Invoice powered by Opygoal Technology Ltd. | Developer: Oladotun Ajakaiye, Service Manager & Data Analyst',
            'bank_details': 'Bank: Sterling Bank | Account No: 0123186628'
        }

        # Initialize paths
        self.logo_path = None
        self.signature_path = None

        # --- Corrected Font Registration for Naira Symbol ---
        # Path to DejaVuSans.ttf (assuming it's in the project root)
        dejavu_font_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'DejaVuSans.ttf')
        self.naira_font_name = 'Helvetica'  # Default fallback font
        self.has_naira_font = False

        try:
            if os.path.exists(dejavu_font_path):
                pdfmetrics.registerFont(TTFont('DejaVuSans', dejavu_font_path))
                self.naira_font_name = 'DejaVuSans'
                self.has_naira_font = True
                print(f"INFO: Successfully registered DejaVuSans font from: {dejavu_font_path}")
            else:
                print(
                    f"WARNING: DejaVuSans.ttf not found at {dejavu_font_path}. Naira sign might not display correctly. Using Helvetica.")
        except Exception as e:
            print(
                f"ERROR: Could not register DejaVuSans font ({e}). Naira sign might not display correctly. Using Helvetica.")
        # --- End Font Registration ---

        self.initUI()

    def initUI(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Create tabs
        tabs = QTabWidget()
        invoice_tab = QWidget()
        receipt_tab = QWidget()

        tabs.addTab(invoice_tab, "Invoice")
        tabs.addTab(receipt_tab, "Receipt")

        # Setup tabs
        self.setup_invoice_tab(invoice_tab)
        self.setup_receipt_tab(receipt_tab)

        layout.addWidget(tabs)

        # Add logo and signature upload buttons
        upload_layout = QHBoxLayout()

        logo_btn = QPushButton("Upload Company Logo")
        logo_btn.clicked.connect(self.upload_logo)
        upload_layout.addWidget(logo_btn)

        signature_btn = QPushButton("Upload Digital Signature")
        signature_btn.clicked.connect(self.upload_signature)
        upload_layout.addWidget(signature_btn)

        layout.addLayout(upload_layout)

    def setup_invoice_tab(self, tab):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        layout = QVBoxLayout(scroll_content)

        # Client Information
        client_group = QGroupBox("Client Information")
        client_layout = QFormLayout()

        self.invoice_client_name = QLineEdit("Mrs Adeola Ajibadade")
        self.invoice_client_address = QTextEdit("Ibadan")
        self.invoice_client_address.setMaximumHeight(60)
        self.invoice_client_contact = QLineEdit("n/a")

        client_layout.addRow("Full Name:", self.invoice_client_name)
        client_layout.addRow("Address:", self.invoice_client_address)
        client_layout.addRow("Contact:", self.invoice_client_contact)

        client_group.setLayout(client_layout)
        layout.addWidget(client_group)

        # Trip Type Selection
        trip_group = QGroupBox("Trip Details")
        trip_layout = QFormLayout()

        self.trip_type = QComboBox()
        self.trip_type.addItems(["Single Trip", "Round Trip"])
        self.trip_type.currentTextChanged.connect(self.update_trip_fields)

        self.pickup_point = QLineEdit("Ibadan")
        self.dropoff_point = QLineEdit("Lekki Phase 1")
        self.trip_date = QDateEdit()
        self.trip_date.setDate(QDate(2025, 9, 11))
        self.trip_date.setCalendarPopup(True)

        self.return_date = QDateEdit()
        self.return_date.setDate(QDate(2025, 9, 13))
        self.return_date.setCalendarPopup(True)
        self.return_date_label = QLabel("Return Date:")

        trip_layout.addRow("Trip Type:", self.trip_type)
        trip_layout.addRow("Pickup Point:", self.pickup_point)
        trip_layout.addRow("Drop Off Point:", self.dropoff_point)
        trip_layout.addRow("Trip Date:", self.trip_date)
        trip_layout.addRow(self.return_date_label, self.return_date)

        trip_group.setLayout(trip_layout)
        layout.addWidget(trip_group)

        # Invoice Details
        invoice_group = QGroupBox("Invoice Details")
        invoice_layout = QFormLayout()

        self.invoice_number = QLineEdit(f"INV-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}")
        self.invoice_date = QDateEdit()
        self.invoice_date.setDate(QDate.currentDate())
        self.invoice_date.setCalendarPopup(True)

        invoice_layout.addRow("Invoice Number:", self.invoice_number)
        invoice_layout.addRow("Date:", self.invoice_date)

        invoice_group.setLayout(invoice_layout)
        layout.addWidget(invoice_group)

        # Services and Pricing
        services_group = QGroupBox("Services and Pricing")
        services_layout = QGridLayout()

        services_layout.addWidget(QLabel("Description"), 0, 0)
        services_layout.addWidget(QLabel("Quantity"), 0, 1)
        services_layout.addWidget(QLabel("Price (N)"), 0, 2)
        services_layout.addWidget(QLabel("Amount (N)"), 0, 3)

        self.service_desc = QLineEdit("Interstate transportation service with Prado Jeep (2013)")
        self.service_qty = QSpinBox()
        self.service_qty.setValue(1)
        self.service_price = QDoubleSpinBox()
        self.service_price.setRange(0, 1000000)
        self.service_price.setValue(250000)
        self.service_amount = QLineEdit()
        self.service_amount.setReadOnly(True)

        services_layout.addWidget(self.service_desc, 1, 0)
        services_layout.addWidget(self.service_qty, 1, 1)
        services_layout.addWidget(self.service_price, 1, 2)
        services_layout.addWidget(self.service_amount, 1, 3)

        # Connect signals for auto-calculation
        self.service_qty.valueChanged.connect(self.calculate_amount)
        self.service_price.valueChanged.connect(self.calculate_amount)
        self.trip_type.currentTextChanged.connect(self.calculate_amount)

        services_group.setLayout(services_layout)
        layout.addWidget(services_group)

        # Notes
        notes_group = QGroupBox("Additional Notes")
        notes_layout = QVBoxLayout()
        self.invoice_notes = QTextEdit()
        self.invoice_notes.setMaximumHeight(80)
        notes_layout.addWidget(self.invoice_notes)
        notes_group.setLayout(notes_layout)
        layout.addWidget(notes_group)

        # Generate button
        generate_btn = QPushButton("Generate Invoice PDF")
        generate_btn.clicked.connect(self.generate_invoice_pdf)
        layout.addWidget(generate_btn)

        scroll_area.setWidget(scroll_content)
        tab_layout = QVBoxLayout(tab)
        tab_layout.addWidget(scroll_area)

        # Initialize trip fields and calculate initial amount
        self.update_trip_fields()
        self.update_notes()
        self.calculate_amount()

    def update_trip_fields(self):
        is_round_trip = self.trip_type.currentText() == "Round Trip"
        self.return_date_label.setVisible(is_round_trip)
        self.return_date.setVisible(is_round_trip)
        self.update_notes()

    def update_notes(self):
        if self.trip_type.currentText() == "Round Trip":
            notes_text = f"Comprehensive interstate transportation service for {self.invoice_client_name.text()} on {self.trip_date.date().toString('MMMM d, yyyy')}, utilizing a dedicated Prado Jeep (2013 Model) and professional driver, for pickup from {self.pickup_point.text()} and direct drop-off at {self.dropoff_point.text()}. Return trip on {self.return_date.date().toString('MMMM d, yyyy')} from {self.dropoff_point.text()} to {self.pickup_point.text()}. All associated travel costs, including fuel, tolls, and standard driver fees, are covered."
        else:
            notes_text = f"Comprehensive interstate transportation service for {self.invoice_client_name.text()} on {self.trip_date.date().toString('MMMM d, yyyy')}, utilizing a dedicated Prado Jeep (2013 Model) and professional driver, for pickup from {self.pickup_point.text()} and direct drop-off at {self.dropoff_point.text()}. All associated travel costs, including fuel, tolls, and standard driver fees, are covered."

        self.invoice_notes.setPlainText(notes_text)

    def setup_receipt_tab(self, tab):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        layout = QVBoxLayout(scroll_content)

        # Receipt Details
        receipt_group = QGroupBox("Receipt Details")
        receipt_layout = QFormLayout()

        self.receipt_number = QLineEdit(f"REC-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}")
        self.receipt_date = QDateEdit()
        self.receipt_date.setDate(QDate.currentDate())
        self.receipt_date.setCalendarPopup(True)

        receipt_layout.addRow("Receipt Number:", self.receipt_number)
        receipt_layout.addRow("Date:", self.receipt_date)

        receipt_group.setLayout(receipt_layout)
        layout.addWidget(receipt_group)

        # Client Information (for receipt)
        client_receipt_group = QGroupBox("Client Information")
        client_receipt_layout = QFormLayout()

        self.receipt_client_name = QLineEdit("Mrs Adeola Ajibadade")
        self.receipt_client_address = QTextEdit("Ibadan")
        self.receipt_client_address.setMaximumHeight(60)
        self.receipt_client_contact = QLineEdit("n/a")

        client_receipt_layout.addRow("Full Name:", self.receipt_client_name)
        client_receipt_layout.addRow("Address:", self.receipt_client_address)
        client_receipt_layout.addRow("Contact:", self.receipt_client_contact)

        client_receipt_group.setLayout(client_receipt_layout)
        layout.addWidget(client_receipt_group)

        # Service Description (for receipt)
        receipt_service_group = QGroupBox("Service Details")
        receipt_service_layout = QFormLayout()

        self.receipt_service_desc = QLineEdit("Payment for Interstate transportation service")
        self.receipt_amount_paid = QDoubleSpinBox()
        self.receipt_amount_paid.setRange(0, 1000000)
        self.receipt_amount_paid.setValue(250000)

        receipt_service_layout.addRow("Description:", self.receipt_service_desc)
        receipt_service_layout.addRow("Amount Paid (N):", self.receipt_amount_paid)

        receipt_service_group.setLayout(receipt_service_layout)
        layout.addWidget(receipt_service_group)

        # Payment Method
        payment_method_group = QGroupBox("Payment Method")
        payment_method_layout = QFormLayout()

        self.receipt_payment_method = QComboBox()
        self.receipt_payment_method.addItems(["Bank Transfer", "Cash", "Card"]) # Added options

        payment_method_layout.addRow("Method:", self.receipt_payment_method)
        payment_method_group.setLayout(payment_method_layout)
        layout.addWidget(payment_method_group)

        # Notes for Receipt
        receipt_notes_group = QGroupBox("Additional Notes")
        receipt_notes_layout = QVBoxLayout()
        self.receipt_notes = QTextEdit("Thank you for your payment.")
        self.receipt_notes.setMaximumHeight(80)
        receipt_notes_layout.addWidget(self.receipt_notes)
        receipt_notes_group.setLayout(receipt_notes_layout)
        layout.addWidget(receipt_notes_group)

        # Generate Receipt button
        generate_receipt_btn = QPushButton("Generate Receipt PDF")
        generate_receipt_btn.clicked.connect(self.generate_receipt_pdf)
        layout.addWidget(generate_receipt_btn)

        scroll_area.setWidget(scroll_content)
        tab_layout = QVBoxLayout(tab)
        tab_layout.addWidget(scroll_area)

    def calculate_amount(self):
        qty = self.service_qty.value()
        price = self.service_price.value()

        # Double the price for round trips
        if self.trip_type.currentText() == "Round Trip":
            price = price * 2
            self.service_desc.setText(f"Round trip interstate transportation service with Prado Jeep (2013)")
        else:
            self.service_desc.setText(f"Single trip interstate transportation service with Prado Jeep (2013)")

        amount = qty * price
        # Conditionally use Naira symbol if font is available
        currency_symbol = '₦' if self.has_naira_font else 'N'
        self.service_amount.setText(f"{currency_symbol}{amount:,.2f}")

    def upload_logo(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Company Logo", "",
                                                   "Image Files (*.png *.jpg *.jpeg *.bmp)")
        if file_path:
            self.logo_path = file_path
            QMessageBox.information(self, "Success", "Logo uploaded successfully!")

    def upload_signature(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Signature Image", "",
                                                   "Image Files (*.png *.jpg *.jpeg *.bmp)")
        if file_path:
            self.signature_path = file_path
            QMessageBox.information(self, "Success", "Signature uploaded successfully!")

    def add_watermark_hologram(self, canvas_obj, doc, text_to_watermark):
        """Add a more visible watermark hologram to the entire PDF page"""
        canvas_obj.saveState()

        # Set a more visible semi-transparent color for the watermark
        canvas_obj.setFillColor(Color(0.2, 0.6, 0.8, alpha=0.15))  # More visible blue color
        canvas_obj.setStrokeColor(Color(0.2, 0.6, 0.8, alpha=0.15))

        # Draw watermark text at an angle across the entire page
        watermark_text = text_to_watermark # Use passed text

        # Create a pattern across the entire page with larger, more visible text
        for x in range(0, int(doc.pagesize[0]), 120):
            for y in range(0, int(doc.pagesize[1]), 100):
                canvas_obj.saveState()
                canvas_obj.translate(x, y)
                canvas_obj.rotate(45)
                canvas_obj.setFont("Helvetica-Bold", 20)  # Larger font size
                canvas_obj.setFillAlpha(0.1)  # More visible
                canvas_obj.drawString(0, 0, watermark_text)
                canvas_obj.restoreState()

        canvas_obj.restoreState()

    def generate_invoice_pdf(self):
        if not all([self.invoice_client_name.text(), self.invoice_client_contact.text()]):
            QMessageBox.warning(self, "Warning", "Please fill in all required client information!")
            return

        file_path, _ = QFileDialog.getSaveFileName(self, "Save Invoice PDF", "", "PDF Files (*.pdf)")
        if not file_path:
            return

        # Create PDF with smaller margins to fit everything on one page
        doc = SimpleDocTemplate(file_path, pagesize=A4,
                                rightMargin=15, leftMargin=15,
                                topMargin=15, bottomMargin=15)

        # Container for the 'Flowable' objects
        elements = []
        styles = getSampleStyleSheet()

        # Define styles using the registered Naira font where appropriate
        normal_font = self.naira_font_name
        bold_font = 'Helvetica-Bold' if normal_font == 'Helvetica' else f'{self.naira_font_name}-Bold'

        # --- Custom Styles for the New Design ---
        # Colors
        primary_blue = HexColor('#3498db')
        light_gray = HexColor('#ecf0f1')
        medium_gray = HexColor('#bdc3c7')
        dark_text = HexColor('#2c3e50')
        light_yellow = HexColor('#fff9e6')
        yellow_border = HexColor('#ffe6b3')

        # Header Styles
        company_name_style = ParagraphStyle(
            'CompanyNameStyle',
            parent=styles['Normal'],
            fontName=bold_font,
            fontSize=18,
            textColor=primary_blue,
            alignment=1,
            spaceAfter=6
        )
        company_address_style = ParagraphStyle(
            'CompanyAddressStyle',
            parent=styles['Normal'],
            fontName=normal_font,
            fontSize=8,
            textColor=dark_text,
            alignment=1,
            spaceAfter=2
        )
        company_contact_style = ParagraphStyle(
            'CompanyContactStyle',
            parent=styles['Normal'],
            fontName=normal_font,
            fontSize=8,
            textColor=dark_text,
            alignment=1,
            spaceAfter=12
        )

        # Invoice Title Style
        invoice_title_style = ParagraphStyle(
            'InvoiceTitleStyle',
            parent=styles['Heading1'],
            fontName=bold_font,
            fontSize=24,
            textColor=primary_blue,
            alignment=1,
            spaceAfter=20
        )

        # Section Header Style (for Bill To, Trip Details, Services, Notes)
        section_header_style = ParagraphStyle(
            'SectionHeaderStyle',
            parent=styles['Heading2'],
            fontName=bold_font,
            fontSize=10,
            textColor=colors.white,
            backColor=primary_blue,
            alignment=0,
            spaceBefore=10,
            spaceAfter=5,
            leftIndent=5,
            rightIndent=5,
            borderPadding=3
        )

        # Details Style (for content within sections)
        details_content_style = ParagraphStyle(
            'DetailsContentStyle',
            parent=styles['Normal'],
            fontName=normal_font,
            fontSize=9,
            textColor=dark_text,
            spaceAfter=2
        )

        # Table Header Style
        table_header_style = ParagraphStyle(
            'TableHeaderStyle',
            parent=styles['Normal'],
            fontName=bold_font,
            fontSize=9,
            textColor=colors.white,
            alignment=1
        )

        # Table Cell Style
        table_cell_style = ParagraphStyle(
            'TableCellStyle',
            parent=styles['Normal'],
            fontName=normal_font,
            fontSize=9,
            textColor=dark_text,
            alignment=0
        )

        # Total Style
        total_label_style = ParagraphStyle(
            'TotalLabelStyle',
            parent=styles['Normal'],
            fontName=bold_font,
            fontSize=10,
            textColor=dark_text,
            alignment=2
        )
        total_amount_style = ParagraphStyle(
            'TotalAmountStyle',
            parent=styles['Normal'],
            fontName=bold_font,
            fontSize=10,
            textColor=primary_blue,
            alignment=2
        )

        # Footer Styles
        footer_bank_style = ParagraphStyle(
            'FooterBankStyle',
            parent=styles['Normal'],
            fontName=bold_font,
            fontSize=9,
            textColor=dark_text,
            alignment=1,
            spaceBefore=10,
            spaceAfter=2
        )
        footer_thankyou_style = ParagraphStyle(
            'FooterThankYouStyle',
            parent=styles['Normal'],
            fontName=normal_font,
            fontSize=10,
            textColor=dark_text,
            alignment=1,
            spaceAfter=2
        )
        footer_tagline_style = ParagraphStyle(
            'FooterTaglineStyle',
            parent=styles['Normal'],
            fontName=bold_font,
            fontSize=8,
            textColor=primary_blue,
            alignment=1,
            spaceAfter=2
        )
        footer_description_style = ParagraphStyle(
            'FooterDescriptionStyle',
            parent=styles['Normal'],
            fontName=normal_font,
            fontSize=7,
            textColor=dark_text,
            alignment=1,
            spaceAfter=10
        )
        footer_copyright_style = ParagraphStyle(
            'FooterCopyrightStyle',
            parent=styles['Normal'],
            fontName=normal_font,
            fontSize=6,
            textColor=colors.grey,
            alignment=1,
            spaceBefore=5
        )

        # --- PDF Generation Layout --- #

        # Define a callback function for the page template to add watermark and footer
        def add_page_elements(canvas_obj, doc):
            self.add_watermark_hologram(canvas_obj, doc, "NextRide & Logistics")

            # Footer (always at the bottom)
            canvas_obj.saveState()
            canvas_obj.setFont(normal_font, 6)
            canvas_obj.setFillColor(colors.grey)
            canvas_obj.drawString(doc.leftMargin, 10, self.company_info['footer'])
            canvas_obj.restoreState()

        # 1. Header Section
        header_elements = []
        if self.logo_path:
            try:
                logo = Image(self.logo_path, width=1.2 * inch, height=0.6 * inch)
                header_elements.append(logo)
            except Exception as e:
                print(f"Error loading logo: {e}")

        header_data = [
            [Paragraph(self.company_info['name'], company_name_style)],
            [Paragraph(self.company_info['address'], company_address_style)],
            [Paragraph(f"Phones: {self.company_info['phones']}", company_contact_style)],
            [Paragraph(f"Emails: {self.company_info['emails']}", company_contact_style)],
        ]

        # Create a table for the header to align logo and company info
        if self.logo_path:
            header_table = Table([
                [Image(self.logo_path, width=1.2 * inch, height=0.6 * inch),
                 Table(header_data, colWidths=[4.5 * inch], rowHeights=[0.2*inch, 0.2*inch, 0.2*inch, 0.2*inch])]
            ], colWidths=[1.5 * inch, 4.5 * inch])
            header_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                ('ALIGN', (1, 0), (1, 0), 'CENTER'),
                ('LEFTPADDING', (1,0), (1,0), 0),
                ('RIGHTPADDING', (1,0), (1,0), 0),
                ('TOPPADDING', (1,0), (1,0), 0),
                ('BOTTOMPADDING', (1,0), (1,0), 0),
            ]))
        else:
            header_table = Table(header_data, colWidths=[6 * inch])
            header_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ]))

        elements.append(header_table)
        elements.append(Spacer(1, 10))

        # Invoice Title and Number/Date
        invoice_info_data = [
            [Paragraph("INVOICE", invoice_title_style)],
            [Paragraph(f"Invoice No: <b>{self.invoice_number.text()}</b>", details_content_style)],
            [Paragraph(f"Date: <b>{self.invoice_date.date().toString('MMMM d, yyyy')}</b>", details_content_style)],
        ]
        invoice_info_table = Table(invoice_info_data, colWidths=[6 * inch])
        invoice_info_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ('TOPPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ]))
        elements.append(invoice_info_table)
        elements.append(Spacer(1, 10))

        # 2. Client Information Section
        elements.append(Paragraph("BILL TO:", section_header_style))
        client_data = [
            [Paragraph(f"<b>Name:</b>", details_content_style), Paragraph(self.invoice_client_name.text(), details_content_style)],
            [Paragraph(f"<b>Address:</b>", details_content_style), Paragraph(self.invoice_client_address.toPlainText(), details_content_style)],
            [Paragraph(f"<b>Contact:</b>", details_content_style), Paragraph(self.invoice_client_contact.text(), details_content_style)],
        ]
        client_table = Table(client_data, colWidths=[1.5 * inch, 4.5 * inch])
        client_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BACKGROUND', (0, 0), (-1, -1), light_gray),
            ('GRID', (0, 0), (-1, -1), 0.5, medium_gray),
            ('PADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(client_table)
        elements.append(Spacer(1, 10))

        # 3. Trip Details Section
        elements.append(Paragraph("TRIP DETAILS:", section_header_style))
        trip_data = [
            [Paragraph(f"<b>Trip Type:</b>", details_content_style), Paragraph(self.trip_type.currentText(), details_content_style)],
            [Paragraph(f"<b>Pickup Point:</b>", details_content_style), Paragraph(self.pickup_point.text(), details_content_style)],
            [Paragraph(f"<b>Drop Off Point:</b>", details_content_style), Paragraph(self.dropoff_point.text(), details_content_style)],
            [Paragraph(f"<b>Trip Date:</b>", details_content_style), Paragraph(self.trip_date.date().toString('MMMM d, yyyy'), details_content_style)],
        ]
        if self.trip_type.currentText() == "Round Trip":
            trip_data.append(
                [Paragraph(f"<b>Return Date:</b>", details_content_style), Paragraph(self.return_date.date().toString('MMMM d, yyyy'), details_content_style)])

        trip_table = Table(trip_data, colWidths=[1.5 * inch, 4.5 * inch])
        trip_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BACKGROUND', (0, 0), (-1, -1), light_gray),
            ('GRID', (0, 0), (-1, -1), 0.5, medium_gray),
            ('PADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(trip_table)
        elements.append(Spacer(1, 10))

        # 4. Services and Pricing Section
        elements.append(Paragraph("SERVICES:", section_header_style))
        qty = self.service_qty.value()
        price = self.service_price.value()
        amount = qty * price
        currency_symbol = '₦' if self.has_naira_font else 'N'

        services_data = [
            [Paragraph('Description', table_header_style),
             Paragraph('Qty', table_header_style),
             Paragraph(f'Price ({currency_symbol})', table_header_style),
             Paragraph(f'Amount ({currency_symbol})', table_header_style)],
            [Paragraph(self.service_desc.text(), table_cell_style),
             Paragraph(str(qty), table_cell_style),
             Paragraph(f"{price:,.2f}", table_cell_style),
             Paragraph(f"{amount:,.2f}", table_cell_style)],
            ['', '', Paragraph('<b>TOTAL:</b>', total_label_style),
             Paragraph(f'<b>{currency_symbol}{amount:,.2f}</b>', total_amount_style)]
        ]

        services_table = Table(services_data, colWidths=[3.5 * inch, 0.7 * inch, 0.9 * inch, 0.9 * inch])
        services_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), primary_blue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), bold_font),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('BACKGROUND', (0, 1), (-1, 1), light_gray),
            ('GRID', (0, 0), (-1, -1), 0.5, medium_gray),
            ('ALIGN', (0, 1), (0, 1), 'LEFT'),
            ('ALIGN', (1, 1), (1, 1), 'CENTER'),
            ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('SPAN', (0, 2), (1, 2)), # Span total label across Description and Qty
            ('BACKGROUND', (0, 2), (-1, 2), light_gray),
            ('TEXTCOLOR', (2, 2), (2, 2), dark_text),
            ('TEXTCOLOR', (3, 2), (3, 2), primary_blue),
            ('FONTNAME', (2, 2), (3, 2), bold_font),
            ('LEFTPADDING', (2,2), (2,2), 0),
            ('RIGHTPADDING', (2,2), (2,2), 0),
            ('TOPPADDING', (2,2), (2,2), 0),
            ('BOTTOMPADDING', (2,2), (2,2), 0),
        ]))
        elements.append(services_table)
        elements.append(Spacer(1, 10))

        # 5. Additional Notes Section
        elements.append(Paragraph("ADDITIONAL NOTES:", section_header_style))
        notes_paragraph = Paragraph(self.invoice_notes.toPlainText(), details_content_style)
        notes_table = Table([[notes_paragraph]], colWidths=[6 * inch])
        notes_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), light_yellow),
            ('GRID', (0, 0), (-1, -1), 0.5, yellow_border),
            ('PADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(notes_table)
        elements.append(Spacer(1, 10))

        # 6. Footer Section
        elements.append(Paragraph(f"<b>Account Details:</b> {self.company_info['bank_details']}", footer_bank_style))
        elements.append(Paragraph("Thank you for your patronage!", footer_thankyou_style))
        elements.append(Paragraph(f"■ {self.company_info['tagline']} ■", footer_tagline_style))
        elements.append(Paragraph(self.company_info['description'], footer_description_style))

        if self.signature_path:
            try:
                signature = Image(self.signature_path, width=1.5 * inch, height=0.75 * inch)
                signature_table = Table([[signature]], colWidths=[6 * inch])
                signature_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 0)
                ]))
                elements.append(signature_table)
                elements.append(Paragraph("Authorized Signature", footer_copyright_style)) # Reusing copyright style for small text
            except Exception as e:
                print(f"Error adding signature: {e}")

        # Build PDF
        doc.build(elements, onFirstPage=add_page_elements, onLaterPages=add_page_elements)

        QMessageBox.information(self, "Success", f"Invoice saved as {file_path}")

    def generate_receipt_pdf(self):
        if not all([self.receipt_client_name.text(), self.receipt_amount_paid.value()]):
            QMessageBox.warning(self, "Warning", "Please fill in all required receipt information!")
            return

        file_path, _ = QFileDialog.getSaveFileName(self, "Save Receipt PDF", "", "PDF Files (*.pdf)")
        if not file_path:
            return

        doc = SimpleDocTemplate(file_path, pagesize=A4,
                                rightMargin=15, leftMargin=15,
                                topMargin=15, bottomMargin=15)

        elements = []
        styles = getSampleStyleSheet()

        normal_font = self.naira_font_name
        bold_font = 'Helvetica-Bold' if normal_font == 'Helvetica' else f'{self.naira_font_name}-Bold'

        # --- Custom Styles for the New Design (Receipt) ---
        primary_blue = HexColor('#3498db')
        light_gray = HexColor('#ecf0f1')
        medium_gray = HexColor('#bdc3c7')
        dark_text = HexColor('#2c3e50')
        light_green = HexColor('#e6ffe6') # A light green for receipt-specific notes
        green_border = HexColor('#b3ffb3') # A green border for receipt-specific notes

        # Header Styles (reused from invoice)
        company_name_style = ParagraphStyle(
            'CompanyNameStyle',
            parent=styles['Normal'],
            fontName=bold_font,
            fontSize=18,
            textColor=primary_blue,
            alignment=1,
            spaceAfter=6
        )
        company_address_style = ParagraphStyle(
            'CompanyAddressStyle',
            parent=styles['Normal'],
            fontName=normal_font,
            fontSize=8,
            textColor=dark_text,
            alignment=1,
            spaceAfter=2
        )
        company_contact_style = ParagraphStyle(
            'CompanyContactStyle',
            parent=styles['Normal'],
            fontName=normal_font,
            fontSize=8,
            textColor=dark_text,
            alignment=1,
            spaceAfter=12
        )

        # Receipt Title Style
        receipt_title_style = ParagraphStyle(
            'ReceiptTitleStyle',
            parent=styles['Heading1'],
            fontName=bold_font,
            fontSize=24,
            textColor=primary_blue,
            alignment=1,
            spaceAfter=20
        )

        # Section Header Style (reused from invoice)
        section_header_style = ParagraphStyle(
            'SectionHeaderStyle',
            parent=styles['Heading2'],
            fontName=bold_font,
            fontSize=10,
            textColor=colors.white,
            backColor=primary_blue,
            alignment=0,
            spaceBefore=10,
            spaceAfter=5,
            leftIndent=5,
            rightIndent=5,
            borderPadding=3
        )

        # Details Style (reused from invoice)
        details_content_style = ParagraphStyle(
            'DetailsContentStyle',
            parent=styles['Normal'],
            fontName=normal_font,
            fontSize=9,
            textColor=dark_text,
            spaceAfter=2
        )

        # Amount Paid Style
        amount_paid_label_style = ParagraphStyle(
            'AmountPaidLabelStyle',
            parent=styles['Normal'],
            fontName=bold_font,
            fontSize=12,
            textColor=dark_text,
            alignment=2
        )
        amount_paid_value_style = ParagraphStyle(
            'AmountPaidValueStyle',
            parent=styles['Normal'],
            fontName=bold_font,
            fontSize=12,
            textColor=primary_blue,
            alignment=2
        )

        # Footer Styles (reused from invoice)
        footer_bank_style = ParagraphStyle(
            'FooterBankStyle',
            parent=styles['Normal'],
            fontName=bold_font,
            fontSize=9,
            textColor=dark_text,
            alignment=1,
            spaceBefore=10,
            spaceAfter=2
        )
        footer_thankyou_style = ParagraphStyle(
            'FooterThankYouStyle',
            parent=styles['Normal'],
            fontName=normal_font,
            fontSize=10,
            textColor=dark_text,
            alignment=1,
            spaceAfter=2
        )
        footer_tagline_style = ParagraphStyle(
            'FooterTaglineStyle',
            parent=styles['Normal'],
            fontName=bold_font,
            fontSize=8,
            textColor=primary_blue,
            alignment=1,
            spaceAfter=2
        )
        footer_description_style = ParagraphStyle(
            'FooterDescriptionStyle',
            parent=styles['Normal'],
            fontName=normal_font,
            fontSize=7,
            textColor=dark_text,
            alignment=1,
            spaceAfter=10
        )
        footer_copyright_style = ParagraphStyle(
            'FooterCopyrightStyle',
            parent=styles['Normal'],
            fontName=normal_font,
            fontSize=6,
            textColor=colors.grey,
            alignment=1,
            spaceBefore=5
        )

        # --- PDF Generation Layout (Receipt) --- #

        def add_page_elements_receipt(canvas_obj, doc):
            self.add_watermark_hologram(canvas_obj, doc, "NextRide & Logistics")

            canvas_obj.saveState()
            canvas_obj.setFont(normal_font, 6)
            canvas_obj.setFillColor(colors.grey)
            canvas_obj.drawString(doc.leftMargin, 10, self.company_info['footer'])
            canvas_obj.restoreState()

        # 1. Header Section (reused from invoice)
        header_elements = []
        if self.logo_path:
            try:
                logo = Image(self.logo_path, width=1.2 * inch, height=0.6 * inch)
                header_elements.append(logo)
            except Exception as e:
                print(f"Error loading logo: {e}")

        header_data = [
            [Paragraph(self.company_info['name'], company_name_style)],
            [Paragraph(self.company_info['address'], company_address_style)],
            [Paragraph(f"Phones: {self.company_info['phones']}", company_contact_style)],
            [Paragraph(f"Emails: {self.company_info['emails']}", company_contact_style)],
        ]

        if self.logo_path:
            header_table = Table([
                [Image(self.logo_path, width=1.2 * inch, height=0.6 * inch),
                 Table(header_data, colWidths=[4.5 * inch], rowHeights=[0.2*inch, 0.2*inch, 0.2*inch, 0.2*inch])]
            ], colWidths=[1.5 * inch, 4.5 * inch])
            header_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                ('ALIGN', (1, 0), (1, 0), 'CENTER'),
                ('LEFTPADDING', (1,0), (1,0), 0),
                ('RIGHTPADDING', (1,0), (1,0), 0),
                ('TOPPADDING', (1,0), (1,0), 0),
                ('BOTTOMPADDING', (1,0), (1,0), 0),
            ]))
        else:
            header_table = Table(header_data, colWidths=[6 * inch])
            header_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ]))

        elements.append(header_table)
        elements.append(Spacer(1, 10))

        # Receipt Title and Number/Date
        receipt_info_data = [
            [Paragraph("RECEIPT", receipt_title_style)],
            [Paragraph(f"Receipt No: <b>{self.receipt_number.text()}</b>", details_content_style)],
            [Paragraph(f"Date: <b>{self.receipt_date.date().toString('MMMM d, yyyy')}</b>", details_content_style)],
        ]
        receipt_info_table = Table(receipt_info_data, colWidths=[6 * inch])
        receipt_info_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ('TOPPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ]))
        elements.append(receipt_info_table)
        elements.append(Spacer(1, 10))

        # 2. Client Information Section (reused from invoice)
        elements.append(Paragraph("RECEIVED FROM:", section_header_style))
        client_data = [
            [Paragraph(f"<b>Name:</b>", details_content_style), Paragraph(self.receipt_client_name.text(), details_content_style)],
            [Paragraph(f"<b>Address:</b>", details_content_style), Paragraph(self.receipt_client_address.toPlainText(), details_content_style)],
            [Paragraph(f"<b>Contact:</b>", details_content_style), Paragraph(self.receipt_client_contact.text(), details_content_style)],
        ]
        client_table = Table(client_data, colWidths=[1.5 * inch, 4.5 * inch])
        client_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BACKGROUND', (0, 0), (-1, -1), light_gray),
            ('GRID', (0, 0), (-1, -1), 0.5, medium_gray),
            ('PADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(client_table)
        elements.append(Spacer(1, 10))

        # 3. Service Details Section (Receipt Specific)
        elements.append(Paragraph("SERVICE DETAILS:", section_header_style))
        currency_symbol = '₦' if self.has_naira_font else 'N'
        amount_paid = self.receipt_amount_paid.value()

        service_details_data = [
            [Paragraph(f"<b>Description:</b>", details_content_style), Paragraph(self.receipt_service_desc.text(), details_content_style)],
            [Paragraph(f"<b>Payment Method:</b>", details_content_style), Paragraph(self.receipt_payment_method.currentText(), details_content_style)],
        ]
        service_details_table = Table(service_details_data, colWidths=[1.5 * inch, 4.5 * inch])
        service_details_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BACKGROUND', (0, 0), (-1, -1), light_gray),
            ('GRID', (0, 0), (-1, -1), 0.5, medium_gray),
            ('PADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(service_details_table)
        elements.append(Spacer(1, 10))

        # Amount Paid Summary
        amount_summary_data = [
            [Paragraph('<b>AMOUNT PAID:</b>', amount_paid_label_style),
             Paragraph(f'<b>{currency_symbol}{amount_paid:,.2f}</b>', amount_paid_value_style)]
        ]
        amount_summary_table = Table(amount_summary_data, colWidths=[4.5 * inch, 1.5 * inch])
        amount_summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), light_gray),
            ('GRID', (0, 0), (-1, -1), 0.5, medium_gray),
            ('PADDING', (0, 0), (-1, -1), 5),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(amount_summary_table)
        elements.append(Spacer(1, 10))

        # 4. Additional Notes Section (Receipt Specific)
        elements.append(Paragraph("ADDITIONAL NOTES:", section_header_style))
        notes_paragraph = Paragraph(self.receipt_notes.toPlainText(), details_content_style)
        notes_table = Table([[notes_paragraph]], colWidths=[6 * inch])
        notes_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), light_green),
            ('GRID', (0, 0), (-1, -1), 0.5, green_border),
            ('PADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(notes_table)
        elements.append(Spacer(1, 10))

        # 5. Footer Section (reused from invoice)
        elements.append(Paragraph(f"<b>Account Details:</b> {self.company_info['bank_details']}", footer_bank_style))
        elements.append(Paragraph("Thank you for your payment!", footer_thankyou_style)) # Changed message
        elements.append(Paragraph(f"■ {self.company_info['tagline']} ■", footer_tagline_style))
        elements.append(Paragraph(self.company_info['description'], footer_description_style))

        if self.signature_path:
            try:
                signature = Image(self.signature_path, width=1.5 * inch, height=0.75 * inch)
                signature_table = Table([[signature]], colWidths=[6 * inch])
                signature_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 0)
                ]))
                elements.append(signature_table)
                elements.append(Paragraph("Authorized Signature", footer_copyright_style))
            except Exception as e:
                print(f"Error adding signature: {e}")

        doc.build(elements, onFirstPage=add_page_elements_receipt, onLaterPages=add_page_elements_receipt)

        QMessageBox.information(self, "Success", f"Receipt saved as {file_path}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = NextRideApp()
    window.show()
    sys.exit(app.exec_())


