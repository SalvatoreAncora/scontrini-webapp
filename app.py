from flask import Flask, render_template, request, redirect, send_file
import os
from werkzeug.utils import secure_filename
from datetime import datetime
from PIL import Image
from openpyxl import load_workbook
from reportlab.pdfgen import canvas
from io import BytesIO

app = Flask(__name__)
UPLOAD_FOLDER = 'static/uploads'
PDF_PATH = 'pdf/scontrini_unificati.pdf'
EXCEL_FILE = '05__Ancora.xlsx'

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
if not os.path.exists('pdf'):
    os.makedirs('pdf')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['scontrino']
    if file.filename == '':
        return 'Nessun file selezionato', 400

    wb = load_workbook(EXCEL_FILE)
    ws = wb.active

    filename = secure_filename(file.filename)
    row_index = None
    euro_importo = request.form.get("importo")
    for row in range(2, ws.max_row + 1):
        if not ws.cell(row=row, column=3).value and ws.cell(row=row, column=2).value == float(euro_importo):
            row_index = row
            break

    if row_index is None:
        return 'Nessuna riga corrispondente trovata nel file Excel.', 400

    nome_file = f"riga_{row_index}.jpg"
    filepath = os.path.join(UPLOAD_FOLDER, nome_file)
    file.save(filepath)

    ws.cell(row=row_index, column=3).value = "Scontrino Allegato"
    wb.save(EXCEL_FILE)

    # Aggiungi al PDF cumulativo
    img = Image.open(filepath)
    c = canvas.Canvas(PDF_PATH, pagesize=(img.width, img.height))
    c.drawInlineImage(filepath, 0, 0)
    c.showPage()
    c.save()

    return redirect('/')

@app.route('/chiudi')
def chiudi():
    return send_file(PDF_PATH, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
