# Invoice and Receipt Generator for NextRide Logistics

A Python application for generating professional invoices and receipts using ReportLab.

## Features

- Generate professional PDF invoices
- Generate PDF receipts
- Customizable company information
- Support for adding logos and signatures
- Nigerian Naira currency formatting

## Requirements

- Python 3.6+
- ReportLab
- Other dependencies (list them if you have a requirements.txt)

## Installation

1. Clone this repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run the script: `python Both_Receipt_Invoice_pdf_generator.py`

## Usage

The script will generate sample invoice and receipt PDF files when run.

Customize the company information in the `HeadlessPDFGenerator` class and provide paths to your logo and signature files using the `set_paths()` method.