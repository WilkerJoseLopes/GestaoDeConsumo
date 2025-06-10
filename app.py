import os
import json
import gspread
from flask import Flask, render_template_string, request, jsonify
from google.oauth2.service_account import Credentials

app = Flask(__name__)

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
try:
    GOOGLE_CREDENTIALS = json.loads(os.getenv("GOOGLE_CREDENTIALS"))
    creds = Credentials.from_service_account_info(GOOGLE_CREDENTIALS, scopes=SCOPES)
    client = gspread.authorize(creds)

    planilha = client.open_by_key("1SKveqiaBaYqyQ5JadM59JKQhd__jodFZfjl78KUGa9w")
    folha_casa = planilha.worksheet("Dados Casa")
except Exception as e:
    print(f"Erro ao inicializar Google Sheets API: {e}")
    client = None
    planilha = None
    folha_casa = None

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Gestão de Consumo</title>
    <meta charset="utf-8" />
    <style>
        #map { height: 600px; width: 100%; }
    </style>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
</head>
<body>
    <h2>Gestão de Consumo</h2>
    <div id="map"></div>
    <br>
    <label>Latitude: <input id="latitude" type="text" /></label>
    <label>Longitude: <input id="longitude" type="text" /></label>
    <button onclick="adicionarMarcador()">Localizar</button>

    <script>
        const map = L.map('map').setView([41.1578, -8.6291], 12);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);

        let marcadorUsuario = null;

        const coresCertificado = {
            'A+': '008000', // verde escuro
            'A': '00AA00',
            'A-': '33BB33',
            'B+': '66CC00',
            'B': '99CC00',
            'B-': 'BBD600',
            'C+': 'CCCC00',
            'C': 'FFFF00',
            'C-': 'FFDD00',
            'D+': 'FFB300',
            'D': 'FFA500',
            'D-': 'FF8800',
            'E+': 'FF6666',
            'E': 'FF0000',
            'E-': 'CC0000',
            'F+': 'A00000',
            'F': '8B0000',
            'F-': '660000',
            'G+': '444444',
            'G': '000000',
            'G-': '222222',
            '': '0000FF' // fallback azul
        };

        function criarIconeCor(corHex) {
            const svg = `
                <svg xmlns="http://www.w3.org/2000/svg" width="32" height="45" viewBox="0 0 32 45">
                    <path fill="#${corHex}" stroke="black" stroke-width="2" d="M16,1 C24.2843,1 31,7.7157 31,16 C31,27 16,44 16,44 C16,44 1,27 1,16 C1,7.7157 7.7157,1 16,1 Z"/>
                </svg>
            `;
            return L.divIcon({
                html: svg,
                iconSize: [32, 45],
                iconAnchor: [16, 44],
                popupAnchor: [0, -40],
                className: ''
            });
        }

        async function adicionarMarcador() {
            const lat = parseFloat(document.getElementById('latitude').value);
            const lng = parseFloat(document.getElementById('longitude').value);

            if (isNaN(lat) || isNaN(lng)) {
                alert("Por favor, insira valores válidos para latitude e longitude.");
                return;
            }

            try {
                const response = await fetch(`/get_certificado?lat=${lat}&lng=${lng}`);
                if (!response.ok) {
                    alert("Erro ao buscar dados do certificado energético.");
                    return;
                }

                const data = await response.json();
                const certificado = (data.certificado || '').trim();
                const corHex = coresCertificado[certificado] || coresCertificado[''];

                if (marcadorUsuario) {
                    map.removeLayer(marcadorUsuario);
                }

                const icone = criarIconeCor(corHex);
                marcadorUsuario = L.marker([lat, lng], {icon: icone}).addTo(map);
                marcadorUsuario.bindPopup(
                    `<div><strong>Minha Casa</strong><br>Latitude: ${lat}<br>Longitude: ${lng}<br>Certificado: <strong>${certificado}</strong><br><button onclick="mostrarInputCodigo()">🔑 Aceder</button><div id="input-codigo-container" style="display:none; margin-top:10px;"><input id="codigo-casa" type="text" placeholder="Código"/></div></div>`
                ).openPopup();

                map.setView([lat, lng], 16);
            } catch (error) {
                alert("Erro na comunicação com o servidor: " + error);
            }
        }

        function mostrarInputCodigo() {
            const c = document.getElementById("input-codigo-container");
            if (c) {
                c.style.display = "block";
                document.getElementById("codigo-casa")?.focus();
            }
        }
    </script>
</body>
</html>
'''


@app.route('/')
def home():
    if folha_casa:
        try:
            folha_casa.get_all_records()
            print("Conexão com Google Sheets verificada com sucesso.")
        except Exception as e:
            print(f"Erro ao acessar Google Sheets: {e}")
    else:
        print("Google Sheets API não inicializada. Verifique suas credenciais.")
    return render_template_string(HTML_TEMPLATE)

@app.route('/get_certificado')
def get_certificado():
    lat = request.args.get('lat', type=float)
    lng = request.args.get('lng', type=float)

    if folha_casa is None or lat is None or lng is None:
        return jsonify({'certificado': ''})

    try:
        registros = folha_casa.get_all_records()
        # Busca registro com latitude e longitude iguais (com arredondamento para 5 casas decimais)
        lat_round = round(lat, 5)
        lng_round = round(lng, 5)

        for reg in registros:
            try:
                reg_lat = round(float(reg.get('Latitude', 0)), 5)
                reg_lng = round(float(reg.get('Longitude', 0)), 5)
                if reg_lat == lat_round and reg_lng == lng_round:
                    cert = reg.get('Certificado Energético', '').strip()
                    return jsonify({'certificado': cert})
            except Exception:
                continue
    except Exception as e:
        print(f"Erro ao buscar dados na planilha: {e}")

    return jsonify({'certificado': ''})

if __name__ == '__main__':
    app.run(debug=True)
