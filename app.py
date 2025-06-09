import os
import json
import gspread
from flask import Flask, render_template_string
from google.oauth2.service_account import Credentials

app = Flask(__name__)

# Configuração do Google Sheets
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
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gestão de Consumo</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        /* CSS REVISADO (DO CÓDIGO FUNCIONAL COM ALTERAÇÕES PARA CABEÇALHO/RODAPÉ ATUAL) */
        html, body {
            margin: 0;
            padding: 0;
            height: 100%; /* Garante que body e html ocupem 100% da viewport */
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f4f7f9;
            color: #333;
            display: flex;
            flex-direction: column; /* Coloca os elementos em coluna */
            min-height: 100vh; /* Ocupa pelo menos a altura da viewport */
            transition: background-color 0.3s, color 0.3s; /* Transição para o tema */
        }

        header {
            background-color: #0077cc;
            color: white;
            padding: 1rem 2rem; /* Mais padding */
            display: flex; /* Flexbox para layout horizontal */
            justify-content: space-between; /* Espaço entre título e botões */
            align-items: center;
        }

        header h1 {
            margin: 0;
            font-weight: 600;
            font-size: 1.8rem;
            text-align: left;
        }
        header h1 a { /* Estilo para o link no título */
            color: white;
            text-decoration: none;
        }
        header h1 a:hover, header h1 a:focus {
            text-decoration: underline;
        }

        #header-right { /* Container para elementos à direita do header */
            display: flex;
            align-items: center;
            gap: 20px;
        }
        #sobre-projeto {
            font-size: 1rem;
            cursor: default;
            user-select: none;
            /* Não há botão de tema ainda, então o estilo é simples */
        }


        main {
            flex: 1; /* Permite que main ocupe o espaço restante */
            padding: 20px;
            max-width: 960px;
            margin: 0 auto;
            box-sizing: border-box; /* Garante que padding não adicione largura */
            width: 100%;
            display: flex; /* Flexbox para layout em coluna */
            flex-direction: column;
            gap: 20px; /* Espaço entre elementos */
        }

        #form-coords {
            text-align: center;
            margin-bottom: 0; /* Removido para usar gap do flexbox */
        }

        input[type="number"], input[type="text"] {
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
            height: 500px; /* Altura fixa essencial */
            width: 100%;
            border-radius: 10px;
            box-shadow: 0 0 12px rgba(0, 0, 0, 0.15);
            background-color: lightgray; /* Adicionado para ver a div mesmo se o mapa não carregar */
        }

        footer {
            background-color: #222;
            color: #ccc;
            text-align: left; /* Alinhamento à esquerda como no seu último código */
            padding: 15px 20px;
            font-size: 0.9em;
            box-sizing: border-box;
            width: 100%;
        }

        /* Media queries para responsividade */
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
        }
    </style>
</head>
<body>
    <header>
        <h1><a href="/">Gestão de Consumo</a></h1>
        <div id="header-right">
            <div id="sobre-projeto" title="Informações sobre o projeto">Sobre o projeto</div>
            </div>
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
        Este sistema é fictício e destina-se exclusivamente a fins académicos e demonstrativos. Nenhuma informação aqui representa dados reais.
    </footer>

    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        // JS DO CÓDIGO FUNCIONAL - MANTIDO SIMPLES
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

            marcadorUsuario.bindPopup(
                `<div id="popup-content">
                    <strong>Minha Casa</strong><br>
                    Latitude: ${lat}<br>
                    Longitude: ${lng}<br><br>
                    <button onclick="mostrarInputCodigo()">🔑 Aceder à Casa</button>
                    <div id="input-codigo-container" style="margin-top: 10px; display: none;">
                        <input type="text" id="codigo-casa" placeholder="Introduza o código">
                    </div>
                </div>`
            ).openPopup();
            map.setView([lat, lng], 16);
        }

        function mostrarInputCodigo() {
            const container = document.getElementById("input-codigo-container");
            if (container) {
                container.style.display = "block";
                // Opcional: focar no input após exibi-lo
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

if __name__ == '__main__':
    app.run(debug=True)
