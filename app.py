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

# HTML completo com header modificado e toggle dark mode
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
        body {
            margin: 0;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f4f7f9;
            color: #333;
            display: flex;
            flex-direction: column;
            min-height: 100vh;
            transition: background-color 0.3s, color 0.3s;
        }

        header {
            background-color: #0077cc;
            color: white;
            padding: 1rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        header h1 {
            margin: 0;
            font-weight: 600;
            font-size: 1.8rem;
            text-align: left;
        }

        #header-right {
            display: flex;
            align-items: center;
            gap: 20px;
        }

        #sobre-projeto {
            font-size: 1rem;
            cursor: default;
            user-select: none;
        }

        #btn-toggle-theme {
            background: none;
            border: none;
            cursor: pointer;
            color: white;
            font-size: 1.4rem;
            padding: 6px 10px;
            border-radius: 6px;
            transition: background-color 0.3s;
        }

        #btn-toggle-theme:hover {
            background-color: rgba(255, 255, 255, 0.2);
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

        input[type='number'],
        input[type='text'] {
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

        /* Dark mode styles */
        body.dark-mode {
            background-color: #121212;
            color: #e0e0e0;
        }

        body.dark-mode header {
            background-color: #1f1f1f;
            color: #e0e0e0;
        }

        body.dark-mode input,
        body.dark-mode button {
            border-color: #555;
            background-color: #222;
            color: #e0e0e0;
        }

        body.dark-mode button {
            background-color: #444;
        }

        body.dark-mode button:hover {
            background-color: #666;
        }

        body.dark-mode #map {
            box-shadow: 0 0 12px rgba(255, 255, 255, 0.15);
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
        }
    </style>
</head>
<body>
    <header>
        <h1>Gestão de Consumo</h1>
        <div id="header-right">
            <div id="sobre-projeto" title="Informações sobre o projeto">Sobre o projeto</div>
            <button id="btn-toggle-theme" aria-label="Alternar modo claro/escuro">🌙</button>
        </div>
    </header>

    <main>
        <div id="form-coords">
            <input
                type="number"
                id="latitude"
                step="any"
                placeholder="Latitude"
            />
            <input
                type="number"
                id="longitude"
                step="any"
                placeholder="Longitude"
            />
            <button onclick="adicionarMarcador()">Mostrar no Mapa</button>
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

        function adicionarMarcador() {
            const lat = parseFloat(document.getElementById('latitude').value);
            const lng = parseFloat(document.getElementById('longitude').value);

            if (isNaN(lat) || isNaN(lng)) {
                alert('Por favor, insira valores válidos para latitude e longitude.');
                return;
            }

            if (marcadorUsuario) {
                map.removeLayer(marcadorUsuario);
            }

            marcadorUsuario = L.marker([lat, lng]).addTo(map);

            marcadorUsuario.bindPopup(\`
                <div id="popup-content">
                    <strong>Minha Casa</strong><br>
                    Latitude: \${lat}<br>
                    Longitude: \${lng}<br><br>
                    <button onclick="mostrarInputCodigo()">🔑 Aceder à Casa</button>
                    <div
                        id="input-codigo-container"
                        style="margin-top: 10px; display: none;"
                    >
                        <input type="text" id="codigo-casa" placeholder="Introduza o código" />
                    </div>
                </div>
            \`).openPopup();

            map.setView([lat, lng], 16);
        }

        function mostrarInputCodigo() {
            const container = document.getElementById('input-codigo-container');
            if (container) {
                container.style.display = 'block';
            }
        }

        // Dark mode toggle
        const btnToggle = document.getElementById('btn-toggle-theme');
        const body = document.body;

        // Carregar preferência salva no localStorage (se houver)
        if (localStorage.getItem('tema') === 'escuro') {
            body.classList.add('dark-mode');
            btnToggle.textContent = '☀️';
        }

        btnToggle.addEventListener('click', () => {
            body.classList.toggle('dark-mode');
            if (body.classList.contains('dark-mode')) {
                btnToggle.textContent = '☀️';
                localStorage.setItem('tema', 'escuro');
            } else {
                btnToggle.textContent = '🌙';
                localStorage.setItem('tema', 'claro');
            }
        });
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
