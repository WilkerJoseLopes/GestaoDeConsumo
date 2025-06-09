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
    with open("templates/index.html", encoding="utf-8") as f:
        return f.read()

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
