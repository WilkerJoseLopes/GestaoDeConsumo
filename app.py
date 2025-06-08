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

# HTML com mapa dinâmico (sem tabelas)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Gestão de Consumo</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        body { font-family: Arial; margin: 20px; }
        #map { height: 500px; width: 90%; margin: 0 auto; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
    </style>
</head>
<body>
    <h1>Gestão de Consumo</h1>

    <!-- Mapa -->
    <div id="map"></div>

    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        // Inicializa o mapa (centrado no Porto)
        const map = L.map('map').setView([41.1578, -8.6291], 12);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);

        // Dados das casas (extraídos da planilha)
        const casas = [
            {casa_dados}
        ];

        // Adiciona marcadores
        casas.forEach(casa => {
            const cor = casa.certificado === 'A+' ? 'green' :
                        casa.certificado === 'A'  ? 'blue' :
                        casa.certificado === 'B+' ? 'orange' :
                        casa.certificado === 'B'  ? 'orange' :
                        casa.certificado === 'B-' ? 'darkorange' :
                        casa.certificado === 'C+' ? 'red' :
                        'gray';

            const icone = L.icon({
                iconUrl: `https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-${cor}.png`,
                iconSize: [25, 41],
                iconAnchor: [12, 41],
                popupAnchor: [0, -30]
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

@app.route('/')
def home():
    dados_casa = folha_casa.get_all_records()

    # Converte em objetos JS
    casas_js = []
    for casa in dados_casa:
        try:
            lat = float(casa.get("Latitude", ""))
            lng = float(casa.get("Longitude", ""))
            descricao = casa.get("Descrição", "")
            morada = casa.get("Morada", "")
            cert = casa.get("Certificado Energético", "")

            casas_js.append(
                f"""{{
                    descricao: "{descricao}",
                    morada: "{morada}",
                    lat: {lat},
                    lng: {lng},
                    certificado: "{cert}"
                }}"""
            )
        except (ValueError, TypeError):
            continue

    casas_str = ",\n            ".join(casas_js)

    return HTML_TEMPLATE.replace("{casa_dados}", casas_str)

if __name__ == '__main__':
    app.run(debug=True)
