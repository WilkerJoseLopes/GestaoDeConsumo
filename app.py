import os
import json
import gspread
from flask import Flask, render_template_string
from google.oauth2.service_account import Credentials

app = Flask(__name__)

# Configuração do Google Sheets
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
GOOGLE_CREDENTIALS = json.loads(os.getenv("GOOGLE_CREDENTIALS"))
creds = Credentials.from_service_account_info(GOOGLE_CREDENTIALS, scopes=SCOPES)
client = gspread.authorize(creds)

planilha = client.open_by_key("1SKveqiaBaYqyQ5JadM59JKQhd__jodFZfjl78KUGa9w")
folha_casa = planilha.worksheet("Dados Casa")

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
        integrity="sha256-o9N1j6kJkR8b0G3LDX0GZmhKQKZ1QwOzv3F3h+PsKro="
        crossorigin=""
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

        header h1 a {
            color: white;
            text-decoration: none;
        }
        header h1 a:hover,
        header h1 a:focus {
            text-decoration: underline;
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
            border: 2px solid white;
            cursor: pointer;
            color: white;
            font-size: 1.2rem;
            padding: 6px 12px;
            border-radius: 6px;
            transition: background-color 0.3s, color 0.3s, border-color 0.3s;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        #btn-toggle-theme:hover,
        #btn-toggle-theme:focus {
            background-color: white;
            color: #0077cc;
            border-color: white;
            outline: none;
        }

        #btn-toggle-theme svg {
            width: 20px;
            height: 20px;
            fill: currentColor;
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
            font-size: 0.9em;
        }

        /* Rodapé com flex para dois lados */
        footer > div {
            max-width: 960px;
            margin: 0 auto;
            padding: 15px 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        #sobre-projeto-footer {
            cursor: pointer;
            user-select: none;
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

        body.dark-mode header h1 a {
            color: #e0e0e0;
        }

        body.dark-mode #sobre-projeto {
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
            footer > div {
                flex-direction: column;
                gap: 10px;
            }
        }
    </style>
</head>
<body>
    <header>
        <h1><a href="/">Gestão de Consumo</a></h1>
        <div id="header-right">
            <div id="sobre-projeto" title="Informações sobre o projeto">Sobre o projeto</div>
            <button id="btn-toggle-theme" aria-label="Alternar modo claro e escuro" title="Alternar modo claro e escuro">
                <!-- ícone sol inicial -->
                <svg id="icon-sun" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display: none;">
                    <circle cx="12" cy="12" r="5"/>
                    <line x1="12" y1="1" x2="12" y2="3"/>
                    <line x1="12" y1="21" x2="12" y2="23"/>
                    <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>
                    <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
                    <line x1="1" y1="12" x2="3" y2="12"/>
                    <line x1="21" y1="12" x2="23" y2="12"/>
                    <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/>
                    <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
                </svg>
                <!-- ícone lua inicial -->
                <svg id="icon-moon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M21 12.79A9 9 0 0112.21 3 7 7 0 0012 21a9 9 0 009-8.21z"/>
                </svg>
            </button>
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
        <div>
          <div>
            Este sistema é fictício e destina-se exclusivamente a fins académicos e demonstrativos.
            Nenhuma informação aqui representa dados reais.
          </div>
          <div id="sobre-projeto-footer">Sobre o projeto</div>
        </div>
    </footer>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
    // Dados recebidos do backend
    const dadosCasas = {{ dados_casas|safe }};

    // Criar mapa e marcar casas da planilha
    const map = L.map('map').setView([41.1578, -8.6291], 12);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map);

    function corDoCertificado(cert) {
        switch(cert) {
            case "A+": return "green";
            case "A": return "limegreen";
            case "B": return "yellow";
            case "C": return "orange";
            case "D": return "red";
            default: return "gray";
        }
    }

    function criarIcone(cor) {
        return L.icon({
            iconUrl: `https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-${cor}.png`,
            shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
            iconSize: [25, 41],
            iconAnchor: [12, 41],
            popupAnchor: [1, -34],
            shadowSize: [41, 41]
        });
    }

    dadosCasas.forEach(casa => {
        if (!isNaN(casa.lat) && !isNaN(casa.lng)) {
            const cor = corDoCertificado(casa.cert);
            const icone = criarIcone(cor);
            const marker = L.marker([casa.lat, casa.lng], {icon: icone}).addTo(map);
            marker.bindPopup(`<strong>Certificado: ${casa.cert}</strong><br>Latitude: ${casa.lat}<br>Longitude: ${casa.lng}`);
        }
    });

    // Marcador do usuário
    let marcadorUsuario = null;

    function adicionarMarcador() {
        const latInput = document.getElementById("latitude");
        const lngInput = document.getElementById("longitude");

        const lat = parseFloat(latInput.value);
        const lng = parseFloat(lngInput.value);

        if (isNaN(lat) || isNaN(lng)) {
            alert("Por favor, insira valores válidos para latitude e longitude.");
            return;
        }

        if (marcadorUsuario) {
            map.removeLayer(marcadorUsuario);
        }

        marcadorUsuario = L.marker([lat, lng]).addTo(map);
        marcadorUsuario.bindPopup("Sua casa").openPopup();

        map.setView([lat, lng], 14);
    }

    // Modo claro/escuro toggle
    const btnTema = document.getElementById("btn-toggle-theme");
    const iconSun = document.getElementById("icon-sun");
    const iconMoon = document.getElementById("icon-moon");

    function atualizarIconeTema() {
        if (document.body.classList.contains("dark-mode")) {
            iconSun.style.display = "inline";
            iconMoon.style.display = "none";
        } else {
            iconSun.style.display = "none";
            iconMoon.style.display = "inline";
        }
    }

    btnTema.addEventListener("click", () => {
        document.body.classList.toggle("dark-mode");
        atualizarIconeTema();
    });

    // Inicializa ícones corretamente
    atualizarIconeTema();

</script>
</body>
</html>
"""

import json

@app.route("/")
def home():
    dados_casas = []
    try:
        registros = folha_casa.get_all_records()
        for r in registros:
            try:
                lat = float(r.get("Latitude", 0))
                lng = float(r.get("Longitude", 0))
                cert = r.get("Certificado", "").strip().upper()
                dados_casas.append({"lat": lat, "lng": lng, "cert": cert})
            except Exception:
                continue
    except Exception:
        # se der erro, continua com lista vazia
        pass

    return render_template_string(HTML_TEMPLATE, dados_casas=json.dumps(dados_casas))


if __name__ == "__main__":
    app.run(debug=True, port=5000)
