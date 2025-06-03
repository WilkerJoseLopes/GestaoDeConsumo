import os
import gspread
from flask import Flask, request, redirect, url_for
from google.oauth2.service_account import Credentials
from datetime import datetime

app = Flask(__name__)

# Configurações do Google Sheets
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SERVICE_ACCOUNT_FILE = 'service_account.json'  # Certifique-se de ter este arquivo no seu projeto

# Template HTML corrigido (substitua com seu template real)
HTML_BASE = """
<!DOCTYPE html>
<html>
<head>
    <title>Gestão de Consumo</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1 { color: #333; }
        table { border-collapse: collapse; width: 100%%; margin-top: 20px; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        form { margin: 20px 0; }
        input, button { padding: 8px; margin: 5px 0; }
    </style>
</head>
<body>
    <h1>Gestão de Consumo</h1>
    %s
</body>
</html>
"""

def get_google_sheet():
    try:
        creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        client = gspread.authorize(creds)
        sheet = client.open_by_key("1SKveqiaBaYqyQ5JadM59JKQhd__jodFZfjl78KUGa9w").sheet1
        return sheet
    except Exception as e:
        print(f"ERRO: {e}")
        return None

@app.route('/', methods=['GET', 'POST'])
def dashboard():
    try:
        sheet = get_google_sheet()
        if not sheet:
            return HTML_BASE % "<h2>Erro: Não foi possível conectar ao Google Sheets</h2>"

        if request.method == 'POST':
            produto = request.form['produto']
            quantidade = request.form['quantidade']
            preco = request.form['preco']
            data = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            sheet.append_row([produto, quantidade, preco, data])
            return redirect(url_for('dashboard'))

        registros = sheet.get_all_records()
        tabela = """
        <form method="POST">
            <input type="text" name="produto" placeholder="Produto" required>
            <input type="number" name="quantidade" placeholder="Quantidade" required>
            <input type="number" step="0.01" name="preco" placeholder="Preço" required>
            <button type="submit">Adicionar</button>
        </form>
        <table>
            <tr>
                <th>Produto</th>
                <th>Quantidade</th>
                <th>Preço</th>
                <th>Data</th>
            </tr>
        """
        
        for registro in registros:
            tabela += f"""
            <tr>
                <td>{registro.get('Produto', '')}</td>
                <td>{registro.get('Quantidade', '')}</td>
                <td>{registro.get('Preço', '')}</td>
                <td>{registro.get('Data', '')}</td>
            </tr>
            """
        
        tabela += "</table>"
        return HTML_BASE % tabela

    except Exception as e:
        error_message = f"<h2>Erro: {str(e)}</h2>"
        if "SERVICE_DISABLED" in str(e):
            error_message += """
            <p>Google Sheets API não está ativada. Ative-a <a href="https://console.developers.google.com/apis/api/sheets.googleapis.com/overview?project=372923049757" target="_blank">aqui</a>.</p>
            """
        return HTML_BASE % error_message

@app.route('/health')
def health():
    return "OK", 200

if __name__ == '__main__':
    app.run(debug=True)
