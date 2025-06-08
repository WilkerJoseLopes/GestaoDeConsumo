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

# Abre a planilha
planilha = client.open_by_key("1SKveqiaBaYqyQ5JadM59JKQhd__jodFZfjl78KUGa9w")
folha_casa = planilha.worksheet("Dados Casa")
folha_consumos = planilha.worksheet("Dados Consumos")

# HTML com mapa dinâmico
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
        #map { height: 500px; width: 90%; margin: 20px auto; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
    </style>
</head>
<body>
    <h1>Gestão de Consumo</h1>
    
    <!-- Mapa -->
    <div id="map"></div>
    
    <!-- Tabelas -->
    <div class="tabela-container">
        <h2>Dados Casa</h2>
        {{ tabela_casa|safe }}
    </div>
    
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        // Inicializa o mapa (centrado no Porto)
        const map = L.map('map').setView([41.1578, -8.6291], 12);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);

        // Dados das casas (extraídos da tabela)
        const casas = [
            {% for casa in casas %}
            {
                descricao: "{{ casa['Descrição'] }}",
                morada: "{{ casa['Morada'] }}",
                lat: {{ casa['Latitude'] }},
                lng: {{ casa['Longitude'] }},
                certificado: "{{ casa['Certificado Energético'] }}"
            },
            {% endfor %}
        ];

        // Adiciona marcadores para cada casa
        casas.forEach(casa => {
            const cor = casa.certificado === 'A+' ? 'green' : 
                       casa.certificado === 'A' ? 'blue' : 'orange';
            
            const icone = L.icon({
                iconUrl: `https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-${cor}.png`,
                iconSize: [25, 41],
                iconAnchor: [12, 41]
            });

            L.marker([casa.lat, casa.lng], { icon: icone })
                .addTo(map)
                .bindPopup(`
                    <b>${casa.descricao}</b><br>
                    ${casa.morada}<br>
                    Certificado: <strong>${casa.certificado}</strong>
                `);
        });
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
    
    # Filtra apenas linhas com latitude/longitude válidos
    casas_validas = [
        casa for casa in dados_casa 
        if isinstance(casa.get('Latitude'), (float, int)) and 
           isinstance(casa.get('Longitude'), (float, int))
    ]
    
    return HTML_TEMPLATE.replace("{{ tabela_casa|safe }}", formatar_dados(dados_casa)) \
                       .replace("{% for casa in casas %}", "") \
                       .replace("{% endfor %}", "") \
                       .replace("{{ casa['Descrição'] }}", "{casa['Descrição']}") \
                       .replace("{{ casa['Morada'] }}", "{casa['Morada']}") \
                       .replace("{{ casa['Latitude'] }}", "{casa['Latitude']}") \
                       .replace("{{ casa['Longitude'] }}", "{casa['Longitude']}") \
                       .replace("{{ casa['Certificado Energético'] }}", "{casa['Certificado Energético']}") \
                       .format(casas=casas_validas)

if __name__ == '__main__':
    app.run(debug=True)
