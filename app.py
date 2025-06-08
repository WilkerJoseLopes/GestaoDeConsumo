import os
import json
import gspread
from flask import Flask
from google.oauth2.service_account import Credentials

app = Flask(__name__)

# Configuração do Google Sheets
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
GOOGLE_CREDENTIALS = json.loads(os.getenv("GOOGLE_CREDENTIALS"))  # Lê do Render
creds = Credentials.from_service_account_info(GOOGLE_CREDENTIALS, scopes=SCOPES)
client = gspread.authorize(creds)

# Abre a planilha pelo ID e a aba "Consumos"
sheet = client.open_by_key("1SKveqiaBaYqyQ5JadM59JKQhd__jodFZfjl78KUGa9w").worksheet("Consumos")

# HTML com tabela para exibir os dados
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Gestão de Consumo</title>
    <style>
        body { font-family: Arial; margin: 20px; }
        table { border-collapse: collapse; width: 80%; margin: 20px auto; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <h1>Dados da Planilha</h1>
    {{ table|safe }}
</body>
</html>
"""

def formatar_dados(dados):
    """Converte os dados da planilha em uma tabela HTML."""
    if not dados:
        return "<p>Nenhum dado encontrado.</p>"
    
    tabela_html = "<table><tr>"
    # Cabeçalhos
    for chave in dados[0].keys():
        tabela_html += f"<th>{chave}</th>"
    tabela_html += "</tr>"
    
    # Linhas
    for linha in dados:
        tabela_html += "<tr>"
        for valor in linha.values():
            tabela_html += f"<td>{valor}</td>"
        tabela_html += "</tr>"
    tabela_html += "</table>"
    return tabela_html

@app.route('/')
def home():
    # Pega todos os dados da aba
    dados = sheet.get_all_records()
    tabela_html = formatar_dados(dados)
    return HTML_TEMPLATE.replace("{{ table|safe }}", tabela_html)

if __name__ == '__main__':
    app.run(debug=True)
