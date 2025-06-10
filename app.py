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
        html, body {
            margin: 0; padding: 0; height: 100%;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            display: flex; flex-direction: column; min-height: 100vh;
            background-color: #f4f7f9; color: #333;
        }
        header {
            background-color: #0077cc; color: white;
            padding: 1rem 2rem; display: flex;
            justify-content: space-between; align-items: center;
            flex-wrap: wrap;
        }
        header h1 {
            margin: 0; font-weight: 600; font-size: 1.8rem;
        }
        header h1 a {
            color: white; text-decoration: none;
        }
        #header-right {
            display: flex; align-items: center; gap: 20px; flex-wrap: wrap;
        }
        #header-right a, #header-right span {
            font-size: 1rem; color: white; text-decoration: none; cursor: pointer;
        }
        #header-right a:hover {
            text-decoration: underline;
        }
        main {
            flex: 1; padding: 20px; max-width: 960px;
            margin: 0 auto; width: 100%; display: flex; flex-direction: column;
            gap: 20px;
        }
        #form-coords {
            text-align: center;
        }
        input[type="number"], input[type="text"] {
            padding: 10px; margin: 8px;
            width: 200px; max-width: 90%;
            border-radius: 6px; border: 1px solid #ccc;
            box-sizing: border-box;
        }
        button {
            padding: 10px 16px; border: none; border-radius: 6px;
            background-color: #0077cc; color: white; cursor: pointer;
        }
        button:hover {
            background-color: #005fa3;
        }
        #map {
            height: 500px; width: 100%; border-radius: 10px;
            box-shadow: 0 0 12px rgba(0,0,0,0.15);
            background-color: lightgray;
        }
        footer {
            background-color: #222; color: #ccc;
            text-align: center; padding: 15px 20px;
            font-size: 0.9em; width: 100%;
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
            input, button {
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
            <a href="https://github.com/WilkerJoseLopes/GestaoDeConsumo" target="_blank" title="Ver projeto no GitHub">Sobre o projeto</a>
            <span title="Entrar (em breve)">Entrar</span>
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

    // Cores em nomes compatíveis com os ícones PNG
    const coresCertificado = {
    'A+': '008000',
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


    // Nova função para usar ícones confiáveis
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
        className: '' // remove classes padrão do Leaflet
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

        const certificado = data.certificado || '';
        const morada = data.morada || 'Morada não disponível';
        const descricao = data.descricao || 'Descrição não disponível';
        const proprietario = data.proprietario || 'Desconhecido';

        const corNome = coresCertificado[certificado] || 'blue';

        if (marcadorUsuario) {
            map.removeLayer(marcadorUsuario);
        }

        const icone = criarIconeCor(corNome);

        marcadorUsuario = L.marker([lat, lng], {icon: icone}).addTo(map);

        marcadorUsuario.bindPopup(
            `<div id="popup-content">
                <strong>${morada}</strong><br>
                <em>${descricao}</em><br><br>
                Latitude: ${lat}<br>
                Longitude: ${lng}<br>
                Certificado Energético: <strong>${certificado}</strong><br><br>
                <button onclick="mostrarInputCodigo()">🔑 Aceder à Casa</button>
                <div id="input-codigo-container" style="margin-top: 10px; display: none;">
                <input type="text" id="codigo-casa" placeholder="Introduza o código" />
                <button onclick="validarCodigo()">Confirmar</button>
                </div>
                <div id="info-proprietario" style="margin-top: 10px; font-weight: bold;"></div>
            </div>`
        ).openPopup();

        map.setView([lat, lng], 16);

        // Função para validar código e mostrar proprietário
        window.validarCodigo = function() {
            const codigoInserido = document.getElementById('codigo-casa').value.trim();
            const infoProp = document.getElementById('info-proprietario');
            if (codigoInserido === 'ademin007') {
                infoProp.textContent = `Proprietário: ${proprietario}`;
            } else {
                infoProp.textContent = 'Código incorreto.';
            }
        };

    } catch (error) {
        alert("Erro na comunicação com o servidor: " + error);
    }
}

    function mostrarInputCodigo() {
        const container = document.getElementById("input-codigo-container");
        if (container) {
            container.style.display = "block";
            const codigoInput = document.getElementById("codigo-casa");
            if (codigoInput) {
                codigoInput.focus();
            }
        }
    }
</script>
</body>
</html>
"""

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
        return jsonify({'certificado': '', 'morada': '', 'descricao': '', 'proprietario': ''})

    try:
        registros = folha_casa.get_all_records()
        
        # Mostrar as colunas da planilha no log para identificar nomes corretos
        if registros:
            print("Colunas disponíveis na planilha:", registros[0].keys())

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
                        # Ajuste aqui o nome da coluna do proprietário depois do teste!
                        'proprietario': reg.get('Proprietário', '').strip()
                    })
            except Exception:
                continue
    except Exception as e:
        print(f"Erro ao buscar dados na planilha: {e}")

    return jsonify({'certificado': '', 'morada': '', 'descricao': '', 'proprietario': ''})


if __name__ == '__main__':
    app.run(debug=True)
