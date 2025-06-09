import os
import json
import gspread
from flask import Flask
from google.oauth2.service_account import Credentials

app = Flask(__name__)

# Configuração Google Sheets (se não quiser usar, pode ignorar)
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
GOOGLE_CREDENTIALS = json.loads(os.getenv("GOOGLE_CREDENTIALS", "{}"))
creds = Credentials.from_service_account_info(GOOGLE_CREDENTIALS, scopes=SCOPES) if GOOGLE_CREDENTIALS else None
client = gspread.authorize(creds) if creds else None

# Abrir planilha - não usado no template
if client:
    planilha = client.open_by_key("1SKveqiaBaYqyQ5JadM59JKQhd__jodFZfjl78KUGa9w")
    folha_casa = planilha.worksheet("Dados Casa")
else:
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
  body {
    margin: 0;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background-color: #f4f7f9;
    color: #333;
    display: flex;
    flex-direction: column;
    min-height: 100vh;
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
  }
  header h1 a {
    color: white;
    text-decoration: none;
  }
  header h1 a:hover,
  header h1 a:focus {
    text-decoration: underline;
  }
  #form-coords {
    text-align: center;
    margin: 20px auto;
  }
  input[type='number'] {
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
    max-width: 960px;
    margin: 0 auto 40px auto;
    border-radius: 10px;
    box-shadow: 0 0 12px rgba(0,0,0,0.15);
  }
  footer {
    background-color: #222;
    color: #ccc;
    text-align: center;
    padding: 15px 10px;
    font-size: 0.9em;
    margin-top: auto;
  }
</style>
</head>
<body>
<header>
  <h1><a href="/">Gestão de Consumo</a></h1>
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
  Este sistema é fictício e destina-se exclusivamente a fins académicos e demonstrativos.
  Nenhuma informação aqui representa dados reais.
</footer>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
  // Esperar DOM carregar antes de rodar mapa
  document.addEventListener("DOMContentLoaded", function() {
    // Inicializa mapa
    const map = L.map('map').setView([41.1578, -8.6291], 12);

    // Adiciona camada de tiles OpenStreetMap
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map);

    let marcadorUsuario = null;

    window.adicionarMarcador = function() {
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

      marcadorUsuario.bindPopup(`
        <div>
          <strong>Minha Casa</strong><br>
          Latitude: ${lat.toFixed(5)}<br>
          Longitude: ${lng.toFixed(5)}<br><br>
          <button id="btn-codigo">🔑 Aceder à Casa</button>
          <div id="input-codigo-container" style="margin-top:10px; display:none;">
            <input type="text" id="codigo-casa" placeholder="Introduza o código" />
            <button id="btn-confirmar-codigo">Confirmar</button>
          </div>
        </div>
      `).openPopup();

      // Espera popup abrir para adicionar eventos
      marcadorUsuario.on("popupopen", function() {
        const btnCodigo = document.getElementById("btn-codigo");
        const inputContainer = document.getElementById("input-codigo-container");
        const btnConfirmar = document.getElementById("btn-confirmar-codigo");

        btnCodigo.onclick = () => {
          inputContainer.style.display = "block";
        };

        btnConfirmar.onclick = () => {
          const codigo = document.getElementById("codigo-casa").value.trim();
          if (!codigo) {
            alert("Por favor, insira o código.");
            return;
          }
          alert("Código inserido: " + codigo);
          inputContainer.style.display = "none";
          marcadorUsuario.closePopup();
        };
      });

      map.setView([lat, lng], 16);
    }
  });
</script>
</body>
</html>
"""

@app.route("/")
def home():
    # Só para "usar" a planilha, mas não está integrado no template
    if folha_casa:
        folha_casa.get_all_records()
    return HTML_TEMPLATE


if __name__ == "__main__":
    app.run(debug=True)
