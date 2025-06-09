import os
import json
import gspread
from flask import Flask, request, jsonify
from google.oauth2.service_account import Credentials
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderUnavailable

app = Flask(__name__)

# Configuração do Google Sheets
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
GOOGLE_CREDENTIALS = json.loads(os.getenv("GOOGLE_CREDENTIALS"))
creds = Credentials.from_service_account_info(GOOGLE_CREDENTIALS, scopes=SCOPES)
client = gspread.authorize(creds)

# Abre a planilha
planilha = client.open_by_key("1SKveqiaBaYqyQ5JadM59JKQhd__jodFZfjl78KUGa9w")
folha_casa = planilha.worksheet("Dados Casa")

# Geolocalização para evitar coordenadas inválidas (ex: no mar)
geolocator = Nominatim(user_agent="gestor_casas")

@app.route("/")
def index():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Gestão de Consumo</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            h1 { color: #333; }
            .container { max-width: 800px; margin: 0 auto; }
            .form-group { margin-bottom: 15px; }
            label { display: block; margin-bottom: 5px; }
            input { padding: 8px; width: 100%; box-sizing: border-box; }
            button { padding: 10px 15px; background: #4CAF50; color: white; border: none; cursor: pointer; }
            button:hover { background: #45a049; }
            #result { margin-top: 20px; padding: 10px; border: 1px solid #ddd; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Gestão de Consumo</h1>
            
            <div class="form-group">
                <label for="latitude">Latitude:</label>
                <input type="text" id="latitude" placeholder="Ex: 38.7223">
            </div>
            
            <div class="form-group">
                <label for="longitude">Longitude:</label>
                <input type="text" id="longitude" placeholder="Ex: -9.1393">
            </div>
            
            <button onclick="verificarCasa()">Verificar Casa</button>
            
            <div id="result"></div>
            
            <div id="acesso" style="display:none; margin-top: 20px;">
                <div class="form-group">
                    <label for="codigo">Código de Acesso:</label>
                    <input type="password" id="codigo">
                </div>
                <button onclick="acessarCasa()">Acessar</button>
            </div>
            
            <script>
                function verificarCasa() {
                    const latitude = document.getElementById('latitude').value;
                    const longitude = document.getElementById('longitude').value;
                    
                    fetch('/verificar_coords', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ latitude, longitude })
                    })
                    .then(response => response.json())
                    .then(data => {
                        const result = document.getElementById('result');
                        if (data.erro) {
                            result.innerHTML = `<p style="color:red">Erro: ${data.erro}</p>`;
                            document.getElementById('acesso').style.display = 'none';
                        } else {
                            result.innerHTML = `<p style="color:green">${data.mensagem}</p>`;
                            document.getElementById('acesso').style.display = 'block';
                        }
                    });
                }
                
                function acessarCasa() {
                    const latitude = document.getElementById('latitude').value;
                    const longitude = document.getElementById('longitude').value;
                    const codigo = document.getElementById('codigo').value;
                    
                    fetch('/aceder_casa', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ latitude, longitude, codigo })
                    })
                    .then(response => response.json())
                    .then(data => {
                        const result = document.getElementById('result');
                        if (data.erro) {
                            result.innerHTML += `<p style="color:red">Erro: ${data.erro}</p>`;
                        } else {
                            result.innerHTML += `<p style="color:green">${data.mensagem} Proprietário: ${data.proprietario}</p>`;
                        }
                    });
                }
            </script>
        </div>
    </body>
    </html>
    """

@app.route("/verificar_coords", methods=["POST"])
def verificar_coords():
    latitude = request.json.get("latitude")
    longitude = request.json.get("longitude")

    try:
        lat = round(float(latitude), 4)
        lon = round(float(longitude), 4)
    except:
        return jsonify({"erro": "Coordenadas inválidas."}), 400

    dados = folha_casa.get_all_records()
    casa = next((c for c in dados if round(float(c["Latitude"]), 4) == lat and round(float(c["Longitude"]), 4) == lon), None)

    if not casa:
        return jsonify({"erro": "Coordenadas não encontradas no sistema."}), 404

    try:
        local = geolocator.reverse(f"{lat}, {lon}", timeout=10)
    except GeocoderUnavailable:
        return jsonify({"erro": "Serviço de geolocalização indisponível."}), 503

    if not local or "ocean" in local.address.lower():
        return jsonify({"erro": "Coordenadas inválidas (localização parece não real)."}), 400

    return jsonify({"mensagem": "Casa encontrada com sucesso."})

@app.route("/aceder_casa", methods=["POST"])
def aceder_casa():
    latitude = request.json.get("latitude")
    longitude = request.json.get("longitude")
    codigo = request.json.get("codigo")

    dados = folha_casa.get_all_records()
    casa = next(
        (c for c in dados if round(float(c["Latitude"]), 4) == round(float(latitude), 4) and
         round(float(c["Longitude"]), 4) == round(float(longitude), 4) and
         str(c["ID"]) == str(codigo)), None
    )

    if not casa:
        return jsonify({"erro": "Código incorreto para esta casa."}), 401

    return jsonify({"mensagem": "Acesso concedido.", "proprietario": casa.get("Proprietários", "Desconhecido")})

if __name__ == "__main__":
    app.run(debug=True)
