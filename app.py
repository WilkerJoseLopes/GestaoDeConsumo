import os
import json
import gspread
from flask import Flask
from google.oauth2.service_account import Credentials

app = Flask(__name__)

# Configuração do Google Sheets
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
GOOGLE_CREDENTIALS = json.loads(os.getenv("GOOGLE_CREDENTIALS"))
creds = Credentials.from_service_account_info(GOOGLE_CREDENTIALS, scopes=SCOPES)
client = gspread.authorize(creds)

# Abre a planilha e as folhas
planilha = client.open_by_key("1SKveqiaBaYqyQ5JadM59JKQhd__jodFZfjl78KUGa9w")
folha_casa = planilha.worksheet("Dados Casa")
folha_consumos = planilha.worksheet("Dados Consumos")

# HTML com mapa (Leaflet) + tabelas
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Gestão de Consumo</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        body { font-family: Arial; margin: 20px; }
        table { border-collapse: collapse; width: 80%; margin: 20px auto; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        .tabela-container { margin-bottom: 40px; }
        #map { height: 400px; width: 80%; margin: 20px auto; border: 1px solid #ccc; }
    </style>
</head>
<body>
    <h1>Gestão de Consumo</h1>
    
    <!-- Mapa com marcador personalizado -->
    <div id="map"></div>
    
    <!-- Tabelas -->
    <div class="tabela-container">
        <h2>Dados Casa</h2>
        {{ tabela_casa|safe }}
    </div>
    
    <div class="tabela-container">
        <h2>Dados Consumos</h2>
        {{ tabela_consumos|safe }}
    </div>

    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        // Configuração do mapa (coordenadas de Lisboa)
        const map = L.map('map').setView([38.7223, -9.1393], 13);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);
        
        // Marcador personalizado (ícone verde)
        const greenIcon = L.icon({
            iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
            iconSize: [25, 41],
            iconAnchor: [12, 41],
            popupAnchor: [1, -34]
        });
        
        L.marker([38.7223, -9.1393], { icon: greenIcon })
            .addTo(map)
            .bindPopup("<b>Localização</b><br>Exemplo em Lisboa");
    </script>
</body>
</html>
"""

def formatar_dados(dados):
    """Converte dados da planilha em tabela HTML."""
    if not dados:
        return "<p>Nenhum dado encontrado.</p>"
    
    tabela_html = "<table><tr>"
    for chave in dados[0].keys():
        tabela_html += f"<th>{chave}</th>"
    tabela_html += "</tr>"
    
    for linha in dados:
        tabela_html += "<tr>"
        for valor in linha.values():
            tabela_html += f"<td>{valor}</td>"
        tabela_html += "</tr>"
    tabela_html += "</table>"
    return tabela_html

@app.route('/')
def home():
    dados_casa = folha_casa.get_all_records()
    dados_consumos = folha_consumos.get_all_records()
    
    return HTML_TEMPLATE.replace("{{ tabela_casa|safe }}", formatar_dados(dados_casa)) \
                       .replace("{{ tabela_consumos|safe }}", formatar_dados(dados_consumos))

if __name__ == '__main__':
    app.run(debug=True)
