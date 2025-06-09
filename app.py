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

# Abre a planilha (mesmo que não use os dados agora)
planilha = client.open_by_key("1SKveqiaBaYqyQ5JadM59JKQhd__jodFZfjl78KUGa9w")
folha_casa = planilha.worksheet("Dados Casa")

# HTML com mapa vazio e formulário de coordenadas
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Gestão de Consumo</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; text-align: center; }
        #map { height: 500px; width: 90%; margin: 20px auto; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
        #form-coords { margin-top: 20px; }
        input[type="number"] {
            padding: 8px;
            margin: 5px;
            width: 150px;
            border: 1px solid #ccc;
            border-radius: 5px;
        }
        button {
            padding: 8px 14px;
            background-color: #007BFF;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }
        button:hover {
            background-color: #0056b3;
        }
    </style>
</head>
<body>
    <h1>Gestão de Consumo</h1>

    <!-- Formulário para inserir coordenadas -->
    <div id="form-coords">
        <input type="number" id="latitude" step="any" placeholder="Latitude">
        <input type="number" id="longitude" step="any" placeholder="Longitude">
        <button onclick="adicionarMarcador()">Mostrar no Mapa</button>
    </div>

    <!-- Mapa -->
    <div id="map"></div>

    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        // Inicializa o mapa centrado no Porto, sem marcadores
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

            // Remove marcador anterior (se houver)
            if (marcadorUsuario) {
                map.removeLayer(marcadorUsuario);
            }

            marcadorUsuario = L.marker([lat, lng])
                .addTo(map)
                .bindPopup(`
                    <b>Minha Casa</b><br>
                    Latitude: ${lat}<br>
                    Longitude: ${lng}<br><br>
                    <button onclick="alert('Página da casa em construção...')">🔑 Aceder à Casa</button>
                `)
                .openPopup();

            map.setView([lat, lng], 16);
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    # Dados ainda são lidos, caso queira usar futuramente
    dados_casa = folha_casa.get_all_records()
    return HTML_TEMPLATE

if __name__ == '__main__':
    app.run(debug=True)
