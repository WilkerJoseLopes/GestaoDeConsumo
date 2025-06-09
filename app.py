import os
import json
import gspread
from flask import Flask, request, render_template_string
from google.oauth2.service_account import Credentials

app = Flask(__name__)

# Configuração Google Sheets
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
GOOGLE_CREDENTIALS = json.loads(os.getenv("GOOGLE_CREDENTIALS"))
creds = Credentials.from_service_account_info(GOOGLE_CREDENTIALS, scopes=SCOPES)
client = gspread.authorize(creds)
planilha = client.open_by_key("1SKveqiaBaYqyQ5JadM59JKQhd__jodFZfjl78KUGa9w")
folha_casa = planilha.worksheet("Dados Casa")
folha_prop = planilha.worksheet("Proprietários")  # <- CORREÇÃO AQUI ✅

# Carregar dados de casa e proprietários
dados_casas = folha_casa.get_all_records()
dados_prop = folha_prop.get_all_records()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
    <title>Gestor de Casas Inteligentes</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
    <style>
        body{margin:0;font-family:Segoe UI,sans-serif;background:#f4f7f9;display:flex;flex-direction:column;min-height:100vh}
        header{background:#0077cc;color:#fff;padding:1rem;text-align:center}
        main{flex:1;padding:20px;max-width:960px;margin:0 auto}
        footer{background:#222;color:#ccc;text-align:center;padding:15px;font-size:.9em}
        #form-coords{text-align:center;margin-bottom:20px}
        input,button{padding:10px;margin:6px;width:200px;max-width:90%;border-radius:6px;border:1px solid #ccc}
        button{background:#0077cc;color:#fff;border:none;cursor:pointer}
        button:hover{background:#005fa3}
        #map{height:500px;width:100%;border-radius:10px;box-shadow:0 0 12px rgba(0,0,0,.15)}
        @media(max-width:600px){#form-coords{display:flex;flex-direction:column;align-items:center}}
        #erro-msg {color: #b00; margin-bottom: 10px;}
        #sucesso-msg {color: #060; margin-bottom: 10px;}
    </style>
</head>
<body>
<header><h1>Gestor de Casas Inteligentes</h1></header>
<main>
    <div id="form-coords">
        <input type="number" id="latitude" step="any" placeholder="Latitude">
        <input type="number" id="longitude" step="any" placeholder="Longitude">
        <button onclick="verificarCasa()">Pesquisar Casa</button>
    </div>
    <div id="erro-msg"></div>
    <div id="sucesso-msg"></div>
    <div id="map"></div>
</main>
<footer>⚠️ Este sistema é fictício e destina-se exclusivamente a fins académicos e demonstrativos.</footer>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
const dadosCasas = {{ casas | safe }};
let map = L.map('map').setView([41.1578, -8.6291], 12);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);
let marcador = null, casaEncontrada = null;

function verificarCasa(){
    const lat = parseFloat(document.getElementById('latitude').value);
    const lng = parseFloat(document.getElementById('longitude').value);
    document.getElementById('erro-msg').innerText = '';
    document.getElementById('sucesso-msg').innerText = '';
    if(isNaN(lat)||isNaN(lng)){
        document.getElementById('erro-msg').innerText = 'Por favor, insira valores válidos.';
        return;
    }
    casaEncontrada = dadosCasas.find(c => parseFloat(c.Latitude) === lat && parseFloat(c.Longitude) === lng);
    if(!casaEncontrada){
        document.getElementById('erro-msg').innerText = 'Localização não encontrada no sistema.';
        return;
    }
    map.setView([lat, lng], 16);
    if(marcador) map.removeLayer(marcador);

    marcador = L.marker([lat,lng]).addTo(map).bindPopup(`
        <strong>${casaEncontrada.Descrição}</strong><br>
        Morada: ${casaEncontrada.Morada}<br><br>
        <button onclick="mostrarAuth()">🔑 Aceder à Casa</button>
        <div id="auth-container" style="display:none; margin-top:10px;">
            <input type="text" id="codigo" placeholder="Código do proprietário">
            <button onclick="validarCodigo()">Entrar</button>
            <div id="auth-msg" style="color:#b00;"></div>
        </div>
    `).openPopup();
}

function mostrarAuth(){
    const c = document.getElementById('auth-container');
    if(c) c.style.display = 'block';
}

function validarCodigo(){
    const codigo = document.getElementById('codigo').value.trim();
    const authMsg = document.getElementById('auth-msg');
    if(codigo === ''){ authMsg.innerText = 'Código obrigatório.'; return; }
    fetch(`/validar?lat=${casaEncontrada.Latitude}&lng=${casaEncontrada.Longitude}&codigo=${codigo}`)
      .then(r=>r.json())
      .then(j=>{
        if(j.sucesso){
            authMsg.style.color='#060';
            authMsg.innerText = `Proprietário: ${j.proprietario}`;
            authMsg.innerHTML += '<br><button onclick="alert(\\'Página da casa em construção...\\')">➡️ Entrar</button>';
        } else {
            authMsg.style.color='#b00';
            authMsg.innerText = j.erro;
        }
      });
}
</script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE, casas=dados_casas)

@app.route('/validar')
def validar():
    lat = request.args.get('lat')
    lng = request.args.get('lng')
    codigo = request.args.get('codigo')
    casa = next((c for c in dados_casas if str(c['Latitude'])==lat and str(c['Longitude'])==lng), None)
    if not casa:
        return {'sucesso': False, 'erro': 'Casa não encontrada.'}
    prop = next((p for p in dados_prop if str(p.get('CasaLat'))==lat and str(p.get('CasaLng'))==lng and p.get('Codigo')==codigo), None)
    if not prop:
        return {'sucesso': False, 'erro': 'Código inválido.'}
    return {'sucesso': True, 'proprietario': prop.get('Nome','Desconhecido')}

if __name__=='__main__':
    app.run(debug=True)
