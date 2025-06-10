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
    <link
        rel="stylesheet"
        href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
    />
    <style>
        html,
        body {
            margin: 0;
            padding: 0;
            height: 100%;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            display: flex;
            flex-direction: column;
            min-height: 100vh;
            background-color: #f4f7f9;
            color: #333;
        }
        header {
            background-color: #0077cc;
            color: white;
            padding: 1rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
        }
        header h1 {
            margin: 0;
            font-weight: 600;
            font-size: 1.8rem;
        }
        header h1 a {
            color: white;
            text-decoration: none;
        }
        #header-right {
            display: flex;
            align-items: center;
            gap: 20px;
            flex-wrap: wrap;
        }
        #header-right a,
        #header-right span {
            font-size: 1rem;
            color: white;
            text-decoration: none;
            cursor: pointer;
        }
        #header-right a:hover {
            text-decoration: underline;
        }
        main {
            flex: 1;
            padding: 20px;
            max-width: 960px;
            margin: 0 auto;
            width: 100%;
            display: flex;
            flex-direction: column;
            gap: 20px;
        }
        #form-coords {
            text-align: center;
        }
        input[type='number'],
        input[type='text'] {
            padding: 10px;
            margin: 8px;
            width: 200px;
            max-width: 90%;
            border-radius: 6px;
            border: 1px solid #ccc;
            box-sizing: border-box;
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
            background-color: lightgray;
        }
        footer {
            background-color: #222;
            color: #ccc;
            text-align: center;
            padding: 15px 20px;
            font-size: 0.9em;
            width: 100%;
        }
        @media (max-width: 600px) {
            header {
                flex-direction: column;
                align-items: flex-start;
                gap: 10px;
                padding: 1rem;
            }
            #header-right {
                width: 100%;
                justify-content: space-between;
            }
            h1 {
                font-size: 1.5em;
            }
            #form-coords {
                display: flex;
                flex-direction: column;
                align-items: center;
            }
            input,
            button {
                width: 90%;
                margin: 6px 0;
            }
            #map {
                height: 300px;
            }
        }
    </style>
</head>
<body>
    <header>
        <h1><a href="/">Gestão de Consumo</a></h1>
        <div id="header-right">
            <a
                href="https://github.com/WilkerJoseLopes/GestaoDeConsumo"
                target="_blank"
                title="Ver projeto no GitHub"
                >Sobre o projeto</a
            >
            <span title="Entrar (em breve)">Entrar</span>
        </div>
    </header>

    <main>
        <div id="form-coords">
            <input type="number" id="latitude" step="any" placeholder="Latitude" />
            <input
                type="number"
                id="longitude"
                step="any"
                placeholder="Longitude"
            />
            <button onclick="buscarCertificadoEAdicionarMarcador()">
                Mostrar no Mapa
            </button>
        </div>

        <div id="map"></div>
    </main>

    <footer>
        Este sistema é fictício e destina-se exclusivamente a fins académicos e
        demonstrativos. Nenhuma informação aqui representa dados reais.
    </footer>

    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        const map = L.map('map').setView([41.1578, -8.6291], 12);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);

        let marcadorUsuario = null;

        // Define cores para cada certificado energético
        const coresCertificado = {
            'A+': 'green',
            'A': 'green',
            'B': 'limegreen',
            'C': 'yellow',
            'D': 'orange',
            'E': 'red',
            'F': 'darkred',
            'G': 'black',
            '': 'blue' // cor padrão caso não tenha certificado
        };

        // Cria um ícone colorido personalizado para o Leaflet
        function criarIconeCor(cor) {
            return L.icon({
                iconUrl:
                    `https://chart.googleapis.com/chart?chst=d_map_pin_letter&chld=%E2%80%A2|${cor.replace(
                        '#',
                        ''
                    )}`,
                iconSize: [21, 34],
                iconAnchor: [10, 34],
                popupAnchor: [0, -34],
                shadowUrl:
                    'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
                shadowSize: [41, 41],
                shadowAnchor: [14, 41]
            });
        }

        async function buscarCertificadoEAdicionarMarcador() {
            const latInput = document.getElementById('latitude');
            const lngInput = document.getElementById('longitude');
            const lat = parseFloat(latInput.value);
            const lng = parseFloat(lngInput.value);

            if (isNaN(lat) || isNaN(lng)) {
                alert('Por favor, insira valores válidos para latitude e longitude.');
                return;
            }

            try {
                const resposta = await fetch(
                    `/buscar_certificado?lat=${lat}&lng=${lng}`
                );
                const dados = await resposta.json();
                const certificado = dados.certificado || '';

                // Decide cor com base no certificado
                let cor = coresCertificado[certificado];
                if (!cor) {
                    cor = 'blue'; // cor padrão
                }

                // Se já existir marcador, remove
                if (marcadorUsuario) {
                    map.removeLayer(marcadorUsuario);
                }

                const icone = criarIconeCor(cor);

                marcadorUsuario = L.marker([lat, lng], { icon: icone }).addTo(map);

                marcadorUsuario.bindPopup(
                    `<div id="popup-content">
                        <strong>Minha Casa</strong><br>
                        Latitude: ${lat}<br>
                        Longitude: ${lng}<br><br>
                        <button onclick="mostrarInputCodigo()">🔑 Aceder à Casa</button>
                        <div id="input-codigo-container" style="margin-top: 10px; display: none;">
                            <input type="text" id="codigo-casa" placeholder="Introduza o código" />
                        </div>
                    </div>`
                ).openPopup();

                map.setView([lat, lng], 16);
            } catch (err) {
                alert('Erro ao buscar certificado energético. Tente novamente.');
                console.error(err);
            }
        }

        function mostrarInputCodigo() {
            const container = document.getElementById('input-codigo-container');
            if (container) {
                container.style.display = 'block';
                const codigoInput = document.getElementById('codigo-casa');
                if (codigoInput) {
                    codigoInput.focus();
                }
            }
        }
    </script>
</body>
</html>
"""

from flask import jsonify

@app.route("/")
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

@app.route("/buscar_certificado")
def buscar_certificado():
    if folha_casa:
        lat = request.args.get("lat", type=float)
        lng = request.args.get("lng", type=float)
        if lat is None or lng is None:
            return jsonify({"certificado": ""})

        try:
            dados = folha_casa.get_all_records()
            # Busca a linha com lat/lng mais próxima (aqui tolerância simples)
            tolerancia = 0.0005  # aprox 50 metros, ajuste conforme necessidade
            for linha in dados:
                try:
                    lat_linha = float(linha.get("Latitude", 0))
                    lng_linha = float(linha.get("Longitude", 0))
                    if abs(lat - lat_linha) <= tolerancia and abs(lng - lng_linha) <= tolerancia:
                        return jsonify({"certificado": linha.get("Certificado Energético", "").strip()})
                except Exception:
                    continue
            return jsonify({"certificado": ""})
        except Exception as e:
            print(f"Erro ao buscar certificado: {e}")
            return jsonify({"certificado": ""})
    else:
        return jsonify({"certificado": ""})

if __name__ == "__main__":
    app.run(debug=True)
