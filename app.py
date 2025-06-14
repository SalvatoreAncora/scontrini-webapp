from flask import Flask, render_template, request, redirect
import pytesseract
from PIL import Image
import openpyxl
from openpyxl import load_workbook
from reportlab.pdfgen import canvas
import os

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
EXCEL_FOLDER = 'excel'
PDF_FILE = 'scontrini_unificati.pdf'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['EXCEL_FOLDER'] = EXCEL_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(EXCEL_FOLDER, exist_ok=True)

@app.route('/')
def index():
    success = request.args.get('success')
    error = request.args.get('error')
    return render_template('index.html', success=success, error=error)

@app.route('/upload_excel', methods=['POST'])
def upload_excel():
    file = request.files.get('excel_file')
    if file:
        file.save(os.path.join(app.config['EXCEL_FOLDER'], 'spese_mensili.xlsx'))
        return redirect('/?success=excel')
    return redirect('/?error=excel')

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files.get('receipt')
    if not file or file.filename == '':
        return redirect('/?error=vuoto')

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(filepath)

    # Estrai testo dallo scontrino
    text = pytesseract.image_to_string(Image.open(filepath))

    # Aggiungi alla PDF unificato
    c = canvas.Canvas(PDF_FILE, bottomup=0)
    c.drawImage(filepath, 50, 100, width=400, preserveAspectRatio=True)
    c.showPage()
    c.save()

    return redirect('/?success=ok')

if __name__ == '__main__':
    app.run(debug=True)
