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
<head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width, initial-scale=1"/><title>Gestão de Consumo</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<style>
html, body {margin:0; padding:0; height:100%}
body {font-family:'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; display:flex; flex-direction:column; min-height:100vh; background-color:#f4f7f9; color:#333;}
header {background-color:#0077cc; color:white; padding:1rem 2rem; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap;}
header h1 {margin:0; font-weight:600; font-size:1.8rem;}
header h1 a {color:white; text-decoration:none;}
#header-right {display:flex; align-items:center; gap:20px; flex-wrap:wrap;}
#header-right a, #header-right span {font-size:1rem; color:white; text-decoration:none; cursor:pointer;}
#header-right a:hover {text-decoration:underline;}
main {flex:1; padding:20px; max-width:960px; margin:0 auto; width:100%; display:flex; flex-direction:column; gap:20px;}
#form-coords {text-align:center;}
input[type="number"], input[type="text"], input[type="password"] {padding:10px; margin:8px; width:200px; max-width:90%; border-radius:6px; border:1px solid #ccc; box-sizing:border-box;}
button {padding:10px 16px; border:none; border-radius:6px; background-color:#0077cc; color:white; cursor:pointer;}
button:hover {background-color:#005fa3;}
#map {height:500px; width:100%; border-radius:10px; box-shadow:0 0 12px rgba(0,0,0,0.15); background-color:lightgray;}
footer {background-color:#222; color:#ccc; text-align:center; padding:15px 20px; font-size:0.9em; width:100%;}
.alert {color:red; font-weight:bold; text-align:center;}
@media (max-width:600px) {
  header {flex-direction:column; align-items:flex-start; gap:10px; padding:1rem;}
  #header-right {width:100%; justify-content:space-between;}
  h1 {font-size:1.5em;}
  #form-coords {display:flex; flex-direction:column; align-items:center;}
  input, button {width:90%; margin:6px 0;}
  #map {height:300px;}
}
</style>
</head>
<body>
<header>
  <h1><a href="/">Gestão de Consumo</a></h1>
  <div id="header-right">
    <a href="https://github.com/WilkerJoseLopes/GestaoDeConsumo" target="_blank">Sobre o projeto</a>
    {% if not session.get('logado') %}
      <a href="/login">Área Privada</a>
    {% else %}
      <span onclick="confirmarLogout()">Logout</span>
    {% endif %}
  </div>
</header>
<main>
  {% if mensagem %}
    <div class="alert">{{ mensagem }}</div>
  {% endif %}
  {% if page == 'login' %}
    <h2 style="text-align:center">Área Privada</h2>
    <form method="POST" style="text-align:center;">
      <input type="password" name="senha" placeholder="Digite a senha" required />
      <br/>
      <button type="submit">Entrar</button>
      <button type="button" onclick="window.location.href='/'">Voltar</button>
    </form>
  {% else %}
    <div id="form-coords">
      <input type="number" id="latitude" step="any" placeholder="Latitude"/>
      <input type="number" id="longitude" step="any" placeholder="Longitude"/>
      <button onclick="adicionarMarcador()">Mostrar no Mapa</button>
    </div>
    <div id="map"></div>
  {% endif %}
</main>
<footer>Este sistema é fictício e destina-se exclusivamente a fins académicos e demonstrativos. Nenhuma informação aqui representa dados reais.</footer>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
function confirmarLogout(){
  if (confirm("Deseja realmente sair?")) {
    window.location.href = "/logout";
  }
}

// Inicializa mapa
const map = L.map('map').setView([41.1578, -8.6291], 12);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);

// Cores por certificado
const cores = {
  'A+':'008000','A':'00AA00','A-':'33BB33','B+':'66CC00','B':'99CC00','B-':'BBD600',
  'C+':'CCCC00','C':'FFFF00','C-':'FFDD00','D+':'FFB300','D':'FFA500','D-':'FF8800',
  'E+':'FF6666','E':'FF0000','E-':'CC0000','F+':'A00000','F':'8B0000','F-':'660000',
  'G+':'444444','G':'000000','G-':'222222','':'0000FF'
};

function criarIcone(c){
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="32" height="45" viewBox="0 0 32 45">
    <path fill="#${c}" stroke="black" stroke-width="2" d="M16,1 C24.3,1 31,7.7 31,16 C31,27 16,44 16,44 C16,44 1,27 1,16 C1,7.7 7.7,1 16,1 Z"/>
  </svg>`;
  return L.divIcon({html: svg, iconSize:[32,45], iconAnchor:[16,44], popupAnchor:[0,-40], className:''});
}

fetch('/todas_casas').then(r=>r.json()).then(casas => {
  casas.forEach(c => {
    const cor = cores[c.certificado]||cores[''];
    const icon = criarIcone(cor);
    const m = L.marker([c.latitude, c.longitude], {icon}).addTo(map);
    let texto = `<strong>${c.morada}</strong><br>
                 ${c.descricao}<br>
                 Latitude: ${c.latitude.toFixed(5)}<br>
                 Longitude: ${c.longitude.toFixed(5)}<br>
                 Certificado: <strong>${c.certificado}</strong>`;
    if (c.proprietario) texto += `<br><em>Proprietário: ${c.proprietario}</em>`;
    m.bindPopup(texto);
  });
});

function adicionarMarcador(){
  const lat = parseFloat(document.getElementById('latitude').value);
  const lng = parseFloat(document.getElementById('longitude').value);
  if(isNaN(lat)||isNaN(lng)){alert('Valores inválidos');return;}
  fetch(`/get_certificado?lat=${lat}&lng=${lng}`).then(r=>r.json()).then(c=>{
    if(!c.latitude){alert('Casa não encontrada'); return;}
    const cor = cores[c.certificado]||cores[''];
    const icon = criarIcone(cor);
    const mark = L.marker([c.latitude,c.longitude],{icon}).addTo(map);
    let texto = `<strong>${c.morada}</strong><br>
                 ${c.descricao}<br>
                 Latitude: ${c.latitude.toFixed(5)}<br>
                 Longitude: ${c.longitude.toFixed(5)}<br>
                 Certificado: <strong>${c.certificado}</strong>`;
    if (c.proprietario) texto += `<br><em>Proprietário: ${c.proprietario}</em>`;
    mark.bindPopup(texto).openPopup();
    map.setView([c.latitude,c.longitude],16);
  }).catch(_=>alert('Erro ao buscar casa'));
}
</script>

<script>
  window.addEventListener('DOMContentLoaded', () => {
    const alertEl = document.querySelector('.alert');
    if(alertEl && alertEl.textContent.trim() !== '') {
      setTimeout(() => {
        alertEl.style.transition = 'opacity 0.5s ease';
        alertEl.style.opacity = '0';
        setTimeout(() => alertEl.remove(), 500);
      }, 2000);
    }
  });
</script>

</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML, session=session, page='index', mensagem=session.pop('mensagem', ''))

@app.route('/login', methods=['GET', 'POST'])
def login():
    mensagem = ''
    if request.method == 'POST':
        if request.form.get('senha') == 'Adming3':
            session['logado'] = True
            session['mensagem'] = 'Login efetuado com sucesso!'
            return redirect('/')
        else:
            mensagem = 'Senha incorreta!'
    return render_template_string(HTML, session=session, page='login', mensagem=mensagem)

@app.route('/logout')
def logout():
    session.clear()
    session['mensagem'] = 'Logout realizado com sucesso.'
    return redirect('/')

@app.route('/todas_casas')
def todas_casas():
    if not folha_casa: return jsonify([])
    regs = folha_casa.get_all_records()
    casas = []
    for reg in regs:
        try:
            casa = {
                'latitude': float(reg.get('Latitude',0)),
                'longitude': float(reg.get('Longitude',0)),
                'morada': reg.get('Morada',''),
                'descricao': reg.get('Descrição',''),
                'certificado': reg.get('Certificado Energético','').strip()
            }
            if session.get('logado'):
                casa['proprietario'] = reg.get('Proprietário', '')
            casas.append(casa)
        except:
            pass
    return jsonify(casas)

@app.route('/get_certificado')
def get_certificado():
    lat = request.args.get('lat', type=float)
    lng = request.args.get('lng', type=float)
    if not folha_casa or lat is None or lng is None: return jsonify({})
    for reg in folha_casa.get_all_records():
        try:
            if abs(float(reg.get('Latitude',0))-lat)<1e-5 and abs(float(reg.get('Longitude',0))-lng)<1e-5:
                casa = {
                    'latitude': float(reg.get('Latitude',0)),
                    'longitude': float(reg.get('Longitude',0)),
                    'morada': reg.get('Morada',''),
                    'descricao': reg.get('Descrição',''),
                    'certificado': reg.get('Certificado Energético','').strip()
                }
                if session.get('logado'):
                    casa['proprietario'] = reg.get('Proprietário', '')
                return jsonify(casa)
        except:
            pass
    return jsonify({})

if __name__ == '__main__':
    app.run(debug=True)
