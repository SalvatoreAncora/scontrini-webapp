
from flask import Flask, render_template, request, redirect
import pytesseract
from PIL import Image
import openpyxl
from openpyxl import load_workbook
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import os
import datetime
import re

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
EXCEL_FOLDER = 'excel'
PDF_FILE = 'scontrini_unificati.pdf'
EXCEL_FILE_NAME = 'spese_mensili.xlsx'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['EXCEL_FOLDER'] = EXCEL_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(EXCEL_FOLDER, exist_ok=True)

def detect_amount_and_currency(text):
    patterns = [
        (r'\€\s?([0-9]+[\.,]?[0-9]*)', 'EUR'),
        (r'\$\s?([0-9]+[\.,]?[0-9]*)', 'USD'),
        (r'\£\s?([0-9]+[\.,]?[0-9]*)', 'GBP'),
    ]
    for pattern, currency in patterns:
        match = re.search(pattern, text)
        if match:
            amount = match.group(1).replace(',', '.')
            return float(amount), currency
    return None, None

def convert_to_eur(amount, currency):
    rates = {
        'EUR': 1.0,
        'USD': 0.92,
        'GBP': 1.17,
    }
    return round(amount * rates.get(currency, 1.0), 2)

def update_excel_with_amount(euro_amount, filename):
    excel_path = os.path.join(EXCEL_FOLDER, EXCEL_FILE_NAME)
    wb = load_workbook(excel_path)
    ws = wb.active
    found = False
    for row in ws.iter_rows(min_row=2):
        cell = row[1]  # assume column B = Importo
        if cell.value is None and not found:
            cell.value = euro_amount
            image_number = cell.row
            found = True
            break
    if found:
        wb.save(excel_path)
        return image_number
    return None

def append_to_pdf(image_path, page_label):
    c = canvas.Canvas(PDF_FILE, pagesize=A4)
    c.drawImage(image_path, 20, 200, width=400, preserveAspectRatio=True)
    c.drawString(20, 50, f"Riga Excel: {page_label}")
    c.showPage()
    c.save()

@app.route('/')
def index():
    success = request.args.get('success')
    error = request.args.get('error')
    return render_template('index.html', success=success, error=error)

@app.route('/upload_excel', methods=['POST'])
def upload_excel():
    file = request.files.get('excel_file')
    if file:
        file.save(os.path.join(EXCEL_FOLDER, EXCEL_FILE_NAME))
        return redirect('/?success=excel')
    return redirect('/?error=excel')

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files.get('receipt')
    if not file or file.filename == '':
        return redirect('/?error=vuoto')

    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    text = pytesseract.image_to_string(Image.open(filepath))
    amount, currency = detect_amount_and_currency(text)
    if amount is None or currency is None:
        return redirect('/?error=ocr')

    euro_amount = convert_to_eur(amount, currency)
    row_number = update_excel_with_amount(euro_amount, filepath)
    if row_number is None:
        return redirect('/?error=riga')

    renamed_path = os.path.join(UPLOAD_FOLDER, f"riga_{row_number}.jpg")
    os.rename(filepath, renamed_path)
    append_to_pdf(renamed_path, row_number)

    return redirect('/?success=scontrino')

if __name__ == '__main__':
    app.run(debug=True)
