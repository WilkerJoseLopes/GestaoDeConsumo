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
        const lon = parseFloat(document.getElementById('longitude').value);

        if (isNaN(lat) || isNaN(lon)) {
            alert('Por favor, insira coordenadas válidas.');
            return;
        }

        if (marcadorUsuario) {
            map.removeLayer(marcadorUsuario);
        }

        marcadorUsuario = L.marker([lat, lon]).addTo(map);

        // Conteúdo do popup com botão que chama função JS separada para funcionar bem
        const popupContent = document.createElement('div');
        popupContent.innerHTML = `
            <h3>Minha casa</h3>
            <p>Está aqui.</p>
        `;

        // Criar botão dinamicamente para funcionar dentro do popup
        const btnCodigo = document.createElement('button');
        btnCodigo.textContent = 'Introduzir Código do Proprietário';
        btnCodigo.style.marginTop = '10px';
        btnCodigo.onclick = mostrarInputCodigo;

        popupContent.appendChild(btnCodigo);

        marcadorUsuario.bindPopup(popupContent).openPopup();

        map.setView([lat, lon], 18);
    }

    function mostrarInputCodigo() {
        const divInput = document.getElementById('input-codigo');
        if (!divInput) {
            // Criar input e botão dinamicamente
            const inputDiv = document.createElement('div');
            inputDiv.id = 'input-codigo';
            inputDiv.style.marginTop = '10px';

            const input = document.createElement('input');
            input.type = 'text';
            input.id = 'codigo-proprietario';
            input.placeholder = 'Digite o código do proprietário';
            input.style.marginRight = '6px';

            const btnConfirmar = document.createElement('button');
            btnConfirmar.textContent = 'Confirmar';
            btnConfirmar.onclick = confirmarCodigo;

            inputDiv.appendChild(input);
            inputDiv.appendChild(btnConfirmar);

            // Adiciona abaixo do botão já existente no popup
            marcadorUsuario.getPopup().getContent().appendChild(inputDiv);

            // Atualiza popup para mostrar novo conteúdo
            marcadorUsuario.getPopup().update();
        }
    }

    function confirmarCodigo() {
        const codigo = document.getElementById('codigo-proprietario').value.trim();
        if (codigo === '') {
            alert('Por favor, insira o código do proprietário.');
            return;
        }

        alert(`Código "${codigo}" recebido. Obrigado!`);
    }

    // Alternar tema claro/escuro
    const btnToggleTheme = document.getElementById('btn-toggle-theme');
    const iconSun = document.getElementById('icon-sun');
    const iconMoon = document.getElementById('icon-moon');

    // Função para salvar preferência no localStorage
    function salvarPreferenciaTema(dark) {
        localStorage.setItem('temaEscuro', dark ? 'true' : 'false');
    }

    // Função para aplicar tema
    function aplicarTema(dark) {
        if (dark) {
            document.body.classList.add('dark-mode');
            iconSun.style.display = 'inline';
            iconMoon.style.display = 'none';
        } else {
            document.body.classList.remove('dark-mode');
            iconSun.style.display = 'none';
            iconMoon.style.display = 'inline';
        }
    }

    // Detectar tema preferido e aplicar ao carregar
    const temaEscuroSalvo = localStorage.getItem('temaEscuro') === 'true';
    aplicarTema(temaEscuroSalvo);

    btnToggleTheme.addEventListener('click', () => {
        const modoAtualEscuro = document.body.classList.contains('dark-mode');
        aplicarTema(!modoAtualEscuro);
        salvarPreferenciaTema(!modoAtualEscuro);
    });
</script>
</body>
</html>
"""

@app.route("/")
def index():
    return HTML_TEMPLATE

if __name__ == "__main__":
    app.run(debug=True)
