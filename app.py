import os
import json
import gspread
from flask import Flask, render_template_string, request, jsonify, session, redirect
from google.oauth2.service_account import Credentials

app = Flask(__name__)
app.secret_key = 'segredo_super_secreto'

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
try:
    GOOGLE_CREDENTIALS = json.loads(os.getenv("GOOGLE_CREDENTIALS"))
    creds = Credentials.from_service_account_info(GOOGLE_CREDENTIALS, scopes=SCOPES)
    client = gspread.authorize(creds)
    planilha = client.open_by_key("1SKveqiaBaYqyQ5JadM59JKQhd__jodFZfjl78KUGa9w")
    folha_casa = planilha.worksheet("Dados Casa")
except Exception as e:
    print("Erro init Google Sheets:", e)
    folha_casa = None

HTML = """<!DOCTYPE html>
<html lang="pt">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>Gestão de Consumo</title>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
  <style>
    html, body {margin:0; padding:0; height:100%}
    body {
      font-family:'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      display:flex; flex-direction:column; min-height:100vh;
      background-color:#f4f7f9; color:#333;
    }
    header {background-color:#0077cc; color:white; padding:1rem 2rem; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap;}
    header h1 {margin:0; font-weight:600; font-size:1.8rem;}
    header h1 a {color:white; text-decoration:none;}
    #header-right {display:flex; align-items:center; gap:20px; flex-wrap:wrap;}
    #header-right a, #header-right span {font-size:1rem; color:white; text-decoration:none; cursor:pointer;}
    main {flex:1; padding:20px; max-width:960px; margin:0 auto; width:100%; display:flex; flex-direction:column; gap:20px;}
    #map {height:500px; width:100%; border-radius:10px; box-shadow:0 0 12px rgba(0,0,0,0.15); background-color:lightgray;}
    .alert {color:red; font-weight:bold; text-align:center;}
    #loginModal {display:none; position:fixed; top:0; left:0; width:100%; height:100%; background-color:rgba(0,0,0,0.5); z-index:1000; justify-content:center; align-items:center;}
    #loginModalContent {background:white; padding:30px; border-radius:10px; box-shadow:0 0 20px rgba(0,0,0,0.2); text-align:center;}
    @media (max-width:600px){
      header{flex-direction:column; align-items:flex-start; gap:10px; padding:1rem;}
      #header-right{width:100%; justify-content:space-between;}
      #map{height:300px;}
    }
    input, button {padding:10px; margin:8px; border-radius:6px; border:1px solid #ccc; box-sizing:border-box;}
    button {background-color:#0077cc; color:white; border:none; cursor:pointer;}
    button:hover{background-color:#005fa3;}
    #search-container {
      display: flex; gap:10px; flex-wrap: wrap; justify-content: center; align-items: center;
      background: #e2eaf1; padding: 15px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1);
    }
    #search-container input {
      width: 150px;
    }
  </style>
</head>
<body>
<header>
  <h1><a href="/">Gestão de Consumo</a></h1>
  <div id="header-right">
    <a href="https://github.com/WilkerJoseLopes/GestaoDeConsumo" target="_blank">Sobre o projeto</a>
    {% if not session.get('logado') %}
      <span onclick="abrirLogin()">Área Privada</span>
    {% else %}
      <span onclick="confirmarLogout()">Logout</span>
    {% endif %}
  </div>
</header>
<main>
  {% if mensagem %}
    <div class="alert">{{ mensagem }}</div>
  {% endif %}

  <!-- Formulário de pesquisa por latitude e longitude -->
  <div id="search-container">
    <label for="latInput">Latitude:</label>
    <input type="number" step="any" id="latInput" placeholder="Ex: 41.1578" />
    <label for="lngInput">Longitude:</label>
    <input type="number" step="any" id="lngInput" placeholder="Ex: -8.6291" />
    <button onclick="irParaCoordenadas()">Ir</button>
  </div>

  <div id="map"></div>
</main>
<div id="loginModal">
  <div id="loginModalContent">
    <h3>Área Privada</h3>
    <input type="password" id="senhaInput" placeholder="Digite a senha" />
    <br/>
    <button onclick="enviarSenha()">Entrar</button>
    <button onclick="fecharLogin()">Cancelar</button>
    <p id="erroSenha" style="color:red; font-weight:bold;"></p>
  </div>
</div>
<footer style="background-color:#0077cc; color:#f5f5f5; padding: 15px; text-align:center; font-weight:bold; font-size:0.95rem;">
  © 2024 Wilker José Lopes – Este sistema é fictício e destina-se exclusivamente a fins académicos e demonstrativos.
</footer>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
// Funções de UI
function confirmarLogout(){
  if(confirm("Deseja realmente sair?")) window.location.href = "/logout";
}
function abrirLogin(){ document.getElementById("loginModal").style.display = "flex"; }
function fecharLogin(){
  document.getElementById("loginModal").style.display = "none";
  document.getElementById("senhaInput").value = "";
  document.getElementById("erroSenha").textContent = "";
}
function enviarSenha(){
  fetch("/verifica_senha", {
    method:"POST", headers:{"Content-Type":"application/json"},
    body:JSON.stringify({senha: document.getElementById("senhaInput").value})
  }).then(r=>r.json()).then(res=>{
    if(res.ok) location.reload();
    else document.getElementById("erroSenha").textContent = "Senha incorreta!";
  });
}

// Configuração do mapa
const map = L.map('map').setView([41.1578, -8.6291], 12);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);

// Dicionário de cores por certificado
const cores = {
  'A+':'008000','A':'00AA00','A-':'33BB33','B+':'66CC00','B':'99CC00','B-':'BBD600',
  'C+':'CCCC00','C':'FFFF00','C-':'FFDD00','D+':'FFB300','D':'FFA500','D-':'FF8800',
  'E+':'FF6666','E':'FF0000','E-':'CC0000','F+':'A00000','F':'8B0000','F-':'660000',
  'G+':'444444','G':'000000','G-':'222222','':'0000FF'
};

// Cria um ícone SVG colorido
function criarIcone(cor){
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="32" height="45" viewBox="0 0 32 45">
      <path fill="#${cor}" stroke="black" stroke-width="2"
        d="M16,1 C24.3,1 31,7.7 31,16 C31,27 16,44 16,44 C16,44 1,27 1,16 C1,7.7 7.7,1 16,1 Z"/>
    </svg>`;
  return L.divIcon({html: svg, iconSize:[32,45], iconAnchor:[16,44], popupAnchor:[0,-40], className:''});
}

// Carrega e plota todas as casas
fetch('/todas_casas')
  .then(r=>r.json())
  .then(casas=>{
    casas.forEach(c=>{
      const cert = (c.certificado||'').toUpperCase().trim();
      const cor = cores[cert] || cores[''];
      const icon = criarIcone(cor);
      const marker = L.marker([c.latitude, c.longitude], {icon}).addTo(map);
      let texto = `<strong>${c.morada}</strong><br>${c.descricao}<br>
                   Lat: ${c.latitude.toFixed(5)}<br>
                   Lng: ${c.longitude.toFixed(5)}<br>
                   Certificado: <strong>${cert}</strong>`;
      if(c.proprietario) texto += `<br><em>Proprietário: ${c.proprietario}</em>`;
      marker.bindPopup(texto);
    });
  });

// Função para ir para as coordenadas inseridas
function irParaCoordenadas(){
  const lat = parseFloat(document.getElementById('latInput').value);
  const lng = parseFloat(document.getElementById('lngInput').value);
  if(!isNaN(lat) && !isNaN(lng)){
    map.setView([lat, lng], 15);
    L.marker([lat, lng]).addTo(map).bindPopup(`Você está aqui:<br>Lat: ${lat.toFixed(5)}<br>Lng: ${lng.toFixed(5)}`).openPopup();
  } else {
    alert('Por favor, insira valores válidos para latitude e longitude.');
  }
}
</script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML,
                                 session=session,
                                 mensagem=session.pop('mensagem', ''))

@app.route('/verifica_senha', methods=['POST'])
def verifica_senha():
    senha = request.json.get('senha')
    if senha == 'Adming3':
        session['logado'] = True
        return jsonify(ok=True)
    return jsonify(ok=False)

@app.route('/logout')
def logout():
    session.clear()
    session['mensagem'] = 'Logout realizado com sucesso.'
    return redirect('/')

@app.route('/todas_casas')
def todas_casas():
    casas = []
    if folha_casa:
        regs = folha_casa.get_all_records()
        for r in regs:
            try:
                lat = float(r.get('Latitude', 0))
                lng = float(r.get('Longitude', 0))
                cert = (r.get('Certificado Energético', '') or '').strip().upper()
                casas.append({
                    'latitude': lat,
                    'longitude': lng,
                    'morada': r.get('Morada', ''),
                    'descricao': r.get('Descrição', ''),
                    'certificado': cert,
                    'proprietario': r.get('Proprietário', '') if session.get('logado') else None
                })
            except:
                continue
    return jsonify(casas)

if __name__ == '__main__':
    app.run(debug=True)
