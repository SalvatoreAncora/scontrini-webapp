from flask import Flask, render_template, request, redirect, send_file
import os
from werkzeug.utils import secure_filename
from PIL import Image
from openpyxl import load_workbook
from reportlab.pdfgen import canvas
import pytesseract
import requests
import re

app = Flask(__name__)
UPLOAD_FOLDER = 'static/uploads'
PDF_PATH = 'pdf/scontrini_unificati.pdf'
EXCEL_FILE = '05__Ancora.xlsx'

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
if not os.path.exists('pdf'):
    os.makedirs('pdf')

def convert_to_euro(amount, currency):
    try:
        url = f"https://api.exchangerate.host/convert?from={currency}&to=EUR&amount={amount}"
        response = requests.get(url)
        result = response.json()
        return result['result']
    except:
        return None

def extract_amount_and_currency(text):
    matches = re.findall(r'(\d+[.,]?\d*)\s?(EUR|USD|CHF|PLN|\$|€|Fr)', text, re.IGNORECASE)
    if matches:
        raw_amount, currency = matches[0]
        amount = float(raw_amount.replace(",", "."))
        if currency in ["€", "EUR"]:
            return amount, "EUR"
        elif currency == "$":
            return amount, "USD"
        elif currency.lower() == "fr":
            return amount, "CHF"
        else:
            return amount, currency.upper()
    return None, None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload_excel', methods=['POST'])
def upload_excel():
    file = request.files['excel']
    if file.filename.endswith('.xlsx'):
        file.save(EXCEL_FILE)
        if os.path.exists(PDF_PATH):
            os.remove(PDF_PATH)
        return redirect('/')
    else:
        return "Formato file non valido. Usa un file .xlsx", 400

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['scontrino']
    if file.filename == '':
        return 'Nessun file selezionato', 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    # OCR + valuta
    img = Image.open(filepath)
    text = pytesseract.image_to_string(img)
    amount, currency = extract_amount_and_currency(text)
    if amount is None or currency is None:
        return "Importo o valuta non riconosciuti nello scontrino", 400

    euro = amount if currency == "EUR" else convert_to_euro(amount, currency)
    if euro is None:
        return "Conversione valuta fallita", 400

    wb = load_workbook(EXCEL_FILE)
    ws = wb.active
    row_index = None
    for row in range(2, ws.max_row + 1):
        if not ws.cell(row=row, column=3).value and abs(ws.cell(row=row, column=2).value - euro) < 0.05:
            row_index = row
            break

    if row_index is None:
        return "Nessuna riga corrispondente trovata nel file Excel.", 400

    image_name = f"riga_{row_index}.jpg"
    saved_path = os.path.join(UPLOAD_FOLDER, image_name)
    img.save(saved_path)

    ws.cell(row=row_index, column=3).value = "Scontrino Allegato"
    wb.save(EXCEL_FILE)

    c = canvas.Canvas(PDF_PATH, pagesize=(img.width, img.height))
    c.drawInlineImage(saved_path, 0, 0)
    c.showPage()
    c.save()

    return redirect('/')

@app.route('/chiudi')
def chiudi():
    return send_file(PDF_PATH, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
