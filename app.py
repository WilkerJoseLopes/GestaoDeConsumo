import os
import json
import gspread
from flask import Flask, render_template_string, jsonify
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

      function obterCorCertificado(certificado) {
        switch (certificado) {
          case 'A+': return 'green';
          case 'A': return 'blue';
          case 'B+': return 'yellow';
          case 'B': return 'orange';
          case 'C+': return 'red';
          case 'C': return 'purple';
          default: return 'gray';
        }
      }

      function adicionarMarcador() {
        const lat = parseFloat(document.getElementById('latitude').value);
        const lng = parseFloat(document.getElementById('longitude').value);

        if (isNaN(lat) || isNaN(lng)) {
          alert('Por favor, insira valores válidos para latitude e longitude.');
          return;
        }

        // Buscar certificado para as coordenadas inseridas
        fetch(`/certificado?lat=${lat}&lng=${lng}`)
          .then(res => res.json())
          .then(data => {
            if (marcadorUsuario) {
              map.removeLayer(marcadorUsuario);
            }

            const cor = obterCorCertificado(data.certificado || '');

            // Criar marcador com cor personalizada
            const icon = L.icon({
              iconUrl: `https://chart.googleapis.com/chart?chst=d_map_pin_letter&chld=%E2%80%A2|${cor.replace('#','')}`,
              iconSize: [21, 34],
              iconAnchor: [10, 34],
              popupAnchor: [0, -34]
            });

            marcadorUsuario = L.marker([lat, lng], {icon}).addTo(map);

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
          })
          .catch(() => {
            alert('Erro ao buscar certificado energético para estas coordenadas.');
          });
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

      // Carregar marcadores da planilha
      function carregarMarcadores() {
        fetch('/dados-casas')
          .then(res => res.json())
          .then(data => {
            data.dados.forEach(item => {
              const lat = parseFloat(item.Latitude);
              const lng = parseFloat(item.Longitude);
              const cert = item['Certificado Energético'] || '';
              const cor = obterCorCertificado(cert);

              // Marcador com círculo colorido
              L.circleMarker([lat, lng], {
                color: cor,
                radius: 8,
                fillOpacity: 0.8,
              }).addTo(map).bindPopup(
                `<strong>${item.Descricao || 'Casa'}</strong><br>` +
                `Certificado Energético: ${cert}<br>` +
                `Proprietário: ${item.Proprietario || 'N/A'}`
              );
            });
          });
      }

      carregarMarcadores();
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

@app.route('/dados-casas')
def dados_casas():
    if folha_casa:
        try:
            dados = folha_casa.get_all_records()
            return jsonify({"dados": dados})
        except Exception as e:
            print(f"Erro ao acessar dados da planilha: {e}")
            return jsonify({"dados": []})
    else:
        return jsonify({"dados": []})

@app.route('/certificado')
def certificado():
    from flask import request
    lat = request.args.get('lat', type=float)
    lng = request.args.get('lng', type=float)

    if folha_casa and lat is not None and lng is not None:
        try:
            dados = folha_casa.get_all_records()
            # Procurar entrada mais próxima (simples busca exata)
            for linha in dados:
                try:
                    lat_linha = float(linha.get("Latitude", 0))
                    lng_linha = float(linha.get("Longitude", 0))
                    if abs(lat - lat_linha) < 0.0001 and abs(lng - lng_linha) < 0.0001:
                        return jsonify({"certificado": linha.get("Certificado Energético", "")})
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
