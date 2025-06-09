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

# Abre a planilha (dados ainda não usados)
planilha = client.open_by_key("1SKveqiaBaYqyQ5JadM59JKQhd__jodFZfjl78KUGa9w")
folha_casa = planilha.worksheet("Dados Casa")

# HTML
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gestor de Casas Inteligentes</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        body {
            margin: 0;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f4f7f9;
            color: #333;
            display: flex;
            flex-direction: column;
            min-height: 100vh;
        }

        header {
            background-color: #0077cc;
            color: white;
            padding: 1rem;
            text-align: center;
        }

        main {
            flex: 1;
            padding: 20px;
            max-width: 960px;
            margin: 0 auto;
        }

        #form-coords {
            text-align: center;
            margin-bottom: 20px;
        }

        input[type="number"], input[type="text"] {
            padding: 10px;
            margin: 8px;
            width: 200px;
            max-width: 90%;
            border-radius: 6px;
            border: 1px solid #ccc;
        }

        button {
            padding: 10px 16px;
            border: none;
            border-radius: 6px;
            background-color: #0077cc;
            color: white;
            cursor: pointer;
        }

        button:hover {
            background-color: #005fa3;
        }

        #map {
            height: 500px;
            width: 100%;
            border-radius: 10px;
            box-shadow: 0 0 12px rgba(0, 0, 0, 0.15);
        }

        footer {
            background-color: #222;
            color: #ccc;
            text-align: center;
            padding: 15px 10px;
            font-size: 0.9em;
        }

        @media (max-width: 600px) {
            h1 {
                font-size: 1.5em;
            }

            #form-coords {
                display: flex;
                flex-direction: column;
                align-items: center;
            }

            input, button {
                width: 90%;
                margin: 6px 0;
            }
        }
    </style>
</head>
<body>
    <header>
        <h1>Gestor de Casas Inteligentes</h1>
    </header>

    <main>
        <div id="form-coords">
            <input type="number" id="latitude" step="any" placeholder="Latitude">
            <input type="number" id="longitude" step="any" placeholder="Longitude">
            <button onclick="adicionarMarcador()">Mostrar no Mapa</button>
        </div>

        <div id="map"></div>
    </main>

    <footer>
        ⚠️ Este sistema é fictício e destina-se exclusivamente a fins académicos e demonstrativos. Nenhuma informação aqui representa dados reais.
    </footer>

    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        const map = L.map('map').setView([41.1578, -8.6291], 12);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);

        let marcadorUsuario = null;

        function adicionarMarcador() {
            const lat = parseFloat(document.getElementById('latitude').value);
            const lng = parseFloat(document.getElementById('longitude').value);

            if (isNaN(lat) || isNaN(lng)) {
                alert("Por favor, insira valores válidos para latitude e longitude.");
                return;
            }

            if (marcadorUsuario) {
                map.removeLayer(marcadorUsuario);
            }

            marcadorUsuario = L.marker([lat, lng]).addTo(map);

            marcadorUsuario.bindPopup(`
                <div id="popup-content">
                    <strong>Minha Casa</strong><br>
                    Latitude: ${lat}<br>
                    Longitude: ${lng}<br><br>
                    <button onclick="mostrarInputCodigo()">🔑 Aceder à Casa</button>
                    <div id="input-codigo-container" style="margin-top: 10px; display: none;">
                        <input type="text" id="codigo-casa" placeholder="Introduza o código">
                    </div>
                </div>
            `).openPopup();

            map.setView([lat, lng], 16);
        }

        function mostrarInputCodigo() {
            const container = document.getElementById("input-codigo-container");
            if (container) {
                container.style.display = "block";
            }
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    # Lê os dados (futuramente usados)
    folha_casa.get_all_records()
    return HTML_TEMPLATE

if __name__ == '__main__':
    app.run(debug=True)
