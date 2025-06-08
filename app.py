import os
import json
import gspread
from flask import Flask
from google.oauth2.service_account import Credentials

app = Flask(__name__)

# Configuração do Google Sheets
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
GOOGLE_CREDENTIALS = json.loads(os.getenv("GOOGLE_CREDENTIALS"))  # Variável do Render
creds = Credentials.from_service_account_info(GOOGLE_CREDENTIALS, scopes=SCOPES)
client = gspread.authorize(creds)

# Abre a planilha e as folhas corretas
planilha = client.open_by_key("1SKveqiaBaYqyQ5JadM59JKQhd__jodFZfjl78KUGa9w")
folha_casa = planilha.worksheet("Dados Casa")          # Nome exato da Folha 01
folha_consumos = planilha.worksheet("Dados Consumos")  # Nome exato da Folha 02

# HTML para exibir os dados
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
        .tabela-container { margin-bottom: 40px; }
    </style>
</head>
<body>
    <h1>Dados da Planilha</h1>
    
    <div class="tabela-container">
        <h2>Dados Casa</h2>
        {{ tabela_casa|safe }}
    </div>
    
    <div class="tabela-container">
        <h2>Dados Consumos</h2>
        {{ tabela_consumos|safe }}
    </div>
</body>
</html>
"""

def formatar_dados(dados):
    """Converte dados da planilha em tabela HTML."""
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
    # Pega dados de ambas as folhas
    dados_casa = folha_casa.get_all_records()
    dados_consumos = folha_consumos.get_all_records()
    
    # Formata as tabelas HTML
    tabela_casa_html = formatar_dados(dados_casa)
    tabela_consumos_html = formatar_dados(dados_consumos)
    
    # Renderiza o template
    return HTML_TEMPLATE.replace("{{ tabela_casa|safe }}", tabela_casa_html) \
                       .replace("{{ tabela_consumos|safe }}", tabela_consumos_html)

if __name__ == '__main__':
    app.run(debug=True)
