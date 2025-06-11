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

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Gestão de Consumo</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        /* Estilos omitidos para encurtar – são os mesmos que você já tinha */
        /* (Você pode manter os estilos CSS que já estavam no seu código anterior) */
    </style>
</head>
<body>
    <header>
        <h1><a href="/">Gestão de Consumo</a></h1>
        <div id="header-right">
            <a href="https://github.com/WilkerJoseLopes/GestaoDeConsumo" target="_blank">Sobre o projeto</a>
            <span>Entrar</span>
        </div>
    </header>

    <main>
        <div id="form-coords">
            <input type="number" id="latitude" step="any" placeholder="Latitude" />
            <input type="number" id="longitude" step="any" placeholder="Longitude" />
            <button onclick="adicionarMarcador()">Mostrar no Mapa</button>
        </div>
        <div id="map"></div>
    </main>

    <footer>
        Este sistema é fictício e destina-se exclusivamente a fins académicos e demonstrativos. Nenhuma informação aqui representa dados reais.
    </footer>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
    const map = L.map('map').setView([41.1578, -8.6291], 12);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);

    let marcadorUsuario = null;

    const coresCertificado = {
        'A+': '008000', 'A': '00AA00', 'A-': '33BB33', 'B+': '66CC00',
        'B': '99CC00', 'B-': 'BBD600', 'C+': 'CCCC00', 'C': 'FFFF00',
        'C-': 'FFDD00', 'D+': 'FFB300', 'D': 'FFA500', 'D-': 'FF8800',
        'E+': 'FF6666', 'E': 'FF0000', 'E-': 'CC0000', 'F+': 'A00000',
        'F': '8B0000', 'F-': '660000', 'G+': '444444', 'G': '000000',
        'G-': '222222', '': '0000FF'
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
                alert("Erro ao buscar dados.");
                return;
            }
            const data = await response.json();

            const certificado = data.certificado || '';
            const morada = data.morada || 'Morada não disponível';
            const descricao = data.descricao || 'Descrição não disponível';
            const proprietario = data.proprietario || 'Desconhecido';
            const cor = coresCertificado[certificado] || '0000FF';

            if (marcadorUsuario) {
                map.removeLayer(marcadorUsuario);
            }

            const icone = criarIconeCor(cor);
            marcadorUsuario = L.marker([lat, lng], { icon: icone }).addTo(map);

            marcadorUsuario.bindPopup(
                `<div>
                    <strong>${morada}</strong><br>
                    <em>${descricao}</em><br><br>
                    Latitude: ${lat}<br>
                    Longitude: ${lng}<br>
                    Certificado: <strong>${certificado}</strong><br><br>
                    <button onclick="mostrarInputCodigo()">🔑 Aceder à Casa</button>
                    <div id="input-codigo-container" style="margin-top: 10px; display: none;">
                        <input type="text" id="codigo-casa" placeholder="Introduza o código" />
                        <button onclick="validarCodigo()">Confirmar</button>
                    </div>
                    <div id="info-proprietario" style="margin-top: 10px; font-weight: bold;"></div>
                </div>`
            ).openPopup();

            map.setView([lat, lng], 16);

            window.validarCodigo = function () {
                const codigo = document.getElementById("codigo-casa").value.trim();
                const info = document.getElementById("info-proprietario");
                if (codigo === "ademin007") {
                    info.textContent = "Proprietário: " + proprietario;
                } else {
                    info.textContent = "Código incorreto.";
                }
            };

        } catch (err) {
            alert("Erro ao carregar dados: " + err);
        }
    }

    function mostrarInputCodigo() {
        const container = document.getElementById("input-codigo-container");
        if (container) {
            container.style.display = "block";
            const input = document.getElementById("codigo-casa");
            if (input) input.focus();
        }
    }

    // 🔁 Carregar todas as casas automaticamente
    async function carregarTodasCasas() {
        try {
            const response = await fetch('/get_all_casas');
            const casas = await response.json();
            casas.forEach(casa => {
                const cor = coresCertificado[casa.certificado] || '0000FF';
                const icone = criarIconeCor(cor);
                const marcador = L.marker([casa.lat, casa.lng], { icon: icone }).addTo(map);
                marcador.bindPopup(
                    `<strong>${casa.morada}</strong><br>
                    <em>${casa.descricao}</em><br>
                    Latitude: ${casa.lat}<br>
                    Longitude: ${casa.lng}<br>
                    Certificado: <strong>${casa.certificado}</strong>`
                );
            });
        } catch (e) {
            console.error("Erro ao carregar casas:", e);
        }
    }

    carregarTodasCasas(); // ⬅️ Iniciar carregamento automático
</script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/get_certificado')
def get_certificado():
    lat = request.args.get('lat', type=float)
    lng = request.args.get('lng', type=float)

    if folha_casa is None or lat is None or lng is None:
        return jsonify({'certificado': '', 'morada': '', 'descricao': '', 'proprietario': ''})

    try:
        registros = folha_casa.get_all_records()
        lat_round = round(lat, 5)
        lng_round = round(lng, 5)
        for reg in registros:
            try:
                reg_lat = round(float(reg.get('Latitude', 0)), 5)
                reg_lng = round(float(reg.get('Longitude', 0)), 5)
                if reg_lat == lat_round and reg_lng == lng_round:
                    return jsonify({
                        'certificado': reg.get('Certificado Energético', '').strip(),
                        'morada': reg.get('Morada', '').strip(),
                        'descricao': reg.get('Descrição', '').strip(),
                        'proprietario': reg.get('Proprietário', '').strip()
                    })
            except:
                continue
    except Exception as e:
        print(f"Erro ao buscar certificado: {e}")

    return jsonify({'certificado': '', 'morada': '', 'descricao': '', 'proprietario': ''})

@app.route('/get_all_casas')
def get_all_casas():
    if folha_casa is None:
        return jsonify([])

    try:
        registros = folha_casa.get_all_records()
        casas = []
        for reg in registros:
            try:
                lat = float(reg.get('Latitude', 0))
                lng = float(reg.get('Longitude', 0))
                casas.append({
                    'lat': lat,
                    'lng': lng,
                    'morada': reg.get('Morada', '').strip(),
                    'descricao': reg.get('Descrição', '').strip(),
                    'certificado': reg.get('Certificado Energético', '').strip(),
                    'proprietario': reg.get('Proprietário', '').strip()
                })
            except:
                continue
        return jsonify(casas)
    except Exception as e:
        print(f"Erro ao buscar casas: {e}")
        return jsonify([])

if __name__ == '__main__':
    app.run(debug=True)
