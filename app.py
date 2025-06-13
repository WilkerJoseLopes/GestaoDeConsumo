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
    folha_consumo = planilha.worksheet("Dados Consumos")
except Exception as e:
    print("Erro init Google Sheets:", e)
    folha_casa = None
    folha_consumo = None

HTML = """<!DOCTYPE html>
<html lang="pt">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>Gestão de Consumo</title>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
  <style>
    html, body {margin:0; padding:0; height:100%; overflow-x:hidden;}
    body {
      font-family:'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      display:flex; flex-direction:column; min-height:100vh;
      background-color:#f4f7f9; color:#333;
      user-select:none; 
    }
    header {
      background-color:#0077cc; color:white;
      padding:1rem 2rem; display:flex;
      justify-content:space-between; align-items:center;
      flex-wrap:wrap;
      user-select:none; 
    }
    header h1 {margin:0; font-weight:600; font-size:1.8rem;}
    header h1 a {color:white; text-decoration:none;}
    #header-right {display:flex; align-items:center; gap:20px; flex-wrap:wrap;}
    #header-right a, #header-right span {
      font-size:1rem; color:white; text-decoration:none; cursor:pointer;
    }
    #header-right a:hover {text-decoration:underline;}
    main {
      flex:1; padding:20px; max-width:960px; margin:0 auto;
      width:100%; display:flex; flex-direction:column; gap:20px;
      user-select:text; 
    }
    #form-coords {text-align:center;}
    input[type="number"], input[type="text"], input[type="password"] {
      padding:10px; margin:8px; width:200px; max-width:90%;
      border-radius:6px; border:1px solid #ccc; box-sizing:border-box;
      user-select:text; 
    }
    button {
      padding:10px 16px; border:none; border-radius:6px;
      background-color:#0077cc; color:white; cursor:pointer;
      user-select:none;
    }
    button:hover {background-color:#005fa3;}
    #map {
      height:500px; width:100%;
      border-radius:10px;
      box-shadow:0 0 12px rgba(0,0,0,0.15);
      background-color:lightgray;
      user-select:none;
    }
    footer {
      background-color:#222; color:#ccc;
      text-align:center; padding:15px 20px; font-size:0.9em;
      width:100%;
      user-select:none; 
    }
    .alert {
      color:geen; font-weight:bold; text-align:center;
      opacity:1;
      transition: opacity 0.7s ease;
    }
    #loginModal {
      display:none; position:fixed; top:0; left:0; width:100%; height:100%;
      background-color:rgba(0,0,0,0.5); z-index:1000;
      justify-content:center; align-items:center;
    }
    #loginModalContent {
      background:white; padding:30px; border-radius:10px;
      box-shadow:0 0 20px rgba(0,0,0,0.2); text-align:center;
    }
    table {
      width:100%; border-collapse:collapse; margin-top:20px;
      background:white; border-radius:8px; overflow:hidden;
      box-shadow:0 0 10px rgba(0,0,0,0.1);
    }
    th, td {
      padding:12px 15px; text-align:left; border-bottom:1px solid #eee;
    }
    th {
      background-color:#0077cc; color:white;
    }
    .consumo-section {
      margin-bottom: 30px;
    }
    .consumo-section h3 {
      color: #0077cc;
      margin-bottom: 10px;
    }
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
      <span onclick="abrirLogin()">Área Privada</span>
    {% else %}
      <span onclick="confirmarLogout()">Logout</span>
    {% endif %}
  </div>
</header>

<main>
  {% if mensagem %}
    <div id="mensagem-alert" class="alert">{{ mensagem }}</div>
  {% endif %}
  <div id="form-coords">
    <input type="number" id="latitude" step="any" placeholder="Latitude"/>
    <input type="number" id="longitude" step="any" placeholder="Longitude"/>
    <button onclick="adicionarMarcador()">Mostrar no Mapa</button>
    <button onclick="limparPesquisa()">Limpar Pesquisa</button>
    <br/>
    <select id="filtroClasse" onchange="filtrarPorClasse()">
      <option value="">Filtrar Certificados Energéticas</option>
      <option value="A+">A+</option>
      <option value="A">A</option>
      <option value="A-">A-</option>
      <option value="B+">B+</option>
      <option value="B">B</option>
      <option value="B-">B-</option>
      <option value="C+">C+</option>
      <option value="C">C</option>
      <option value="C-">C-</option>
      <option value="D+">D+</option>
      <option value="D">D</option>
      <option value="D-">D-</option>
      <option value="E+">E+</option>
      <option value="E">E</option>
      <option value="E-">E-</option>
      <option value="F+">F+</option>
      <option value="F">F</option>
      <option value="F-">F-</option>
      <option value="G+">G+</option>
      <option value="G">G</option>
      <option value="G-">G-</option>
    </select>
  </div>
  <div id="map"></div>

  {% if session.get('logado') %}
    <div id="consumos"></div>
  {% endif %}
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

<footer>
  Este sistema é fictício e destina-se exclusivamente a fins académicos e demonstrativos. Os dados apresentados são fictícios e para fins de demonstração.
</footer>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
function confirmarLogout(){
  if (confirm("Deseja realmente sair?")) {
    window.location.href = "/logout";
  }
}
function abrirLogin(){
  document.getElementById("loginModal").style.display = "flex";
}
function fecharLogin(){
  document.getElementById("loginModal").style.display = "none";
  document.getElementById("senhaInput").value = "";
  document.getElementById("erroSenha").textContent = "";
}
function enviarSenha(){
  const senha = document.getElementById("senhaInput").value;
  fetch("/verifica_senha", {
    method:"POST",
    headers:{"Content-Type":"application/json"},
    body:JSON.stringify({senha})
  })
  .then(r=>r.json())
  .then(res=>{
    if(res.ok){
      location.reload();
    } else {
      document.getElementById("erroSenha").textContent = "Senha incorreta!";
    }
  });
}

const map = L.map('map').setView([41.1578, -8.6291], 12);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);

const cores = {
  'A+':'008000','A':'00AA00','A-':'33BB33','B+':'66CC00','B':'99CC00','B-':'BBD600',
  'C+':'CCCC00','C':'FFFF00','C-':'FFDD00','D+':'FFB300','D':'FFA500','D-':'FF8800',
  'E+':'FF6666','E':'FF0000','E-':'CC0000','F+':'A00000','F':'8B0000','F-':'660000',
  'G+':'444444','G':'000000','G-':'222222','':'0000FF'
};

function criarIcone(cor){
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="32" height="45" viewBox="0 0 32 45">
      <path fill="#${cor}" stroke="black" stroke-width="2" d="M16,1 C24.3,1 31,7.7 31,16 C31,28 16,44 16,44 C16,44 1,28 1,16 C1,7.7 7.7,1 16,1 Z"/>
    </svg>`;
  return L.divIcon({
    html: svg,
    className: '',
    iconSize: [32,45],
    iconAnchor: [16,44],
    popupAnchor: [0,-40]
  });
}

let markers = [];

function limparMarkers(){
  markers.forEach(m => map.removeLayer(m));
  markers = [];
}

function carregarCasas(){
  fetch("/todas_casas").then(r=>r.json()).then(data=>{
    limparMarkers();
    data.forEach(casa=>{
      const cor = cores[casa.certificado.trim()] || cores[''];
      const icon = criarIcone(cor);
      const marker = L.marker([casa.latitude, casa.longitude], {icon}).addTo(map);
      let texto = `<strong>${casa.morada}</strong><br>${casa.descricao}<br>
                   Latitude: ${casa.latitude.toFixed(5)}<br>
                   Longitude: ${casa.longitude.toFixed(5)}<br>
                   Certificado: <strong>${casa.certificado}</strong>`;
      if(casa.proprietario) texto += `<br><em>Proprietário: ${casa.proprietario}</em>`;
      marker.bindPopup(texto);
      marker.on('click', () => {
        marker.openPopup();
        if({{ 'true' if session.get('logado') else 'false' }}) {
          carregarConsumos(casa.id);
        }
      });
      markers.push(marker);
    });
  });
}

function carregarConsumos(idCasa){
  fetch("/consumos?id="+idCasa).then(r=>r.json()).then(data=>{
    const consumosDiv = document.getElementById("consumos");
    if(data.agua.length === 0 && data.energia.length === 0 && data.gas.length === 0){
      consumosDiv.innerHTML = "<p>Nenhum consumo encontrado para esta casa.</p>";
      return;
    }
    
    let html = '<div style="display: flex; flex-direction: column; gap: 30px;">';
    
    // Água
    if(data.agua.length > 0){
      html += `<div class="consumo-section">
        <h3>Consumo de Água</h3>
        <table>
          <thead>
            <tr>
              <th>Período</th>
              <th>Valor</th>
              <th>Custo (€)</th>
            </tr>
          </thead>
          <tbody>`;
      
      data.agua.forEach(c=>{
        html += `<tr>
          <td>${c.periodo}</td>
          <td>${c.valor} ${c.unidade}</td>
          <td>${c.custo}</td>
        </tr>`;
      });
      
      html += `</tbody>
        </table>
      </div>`;
    }
    
    // Energia
    if(data.energia.length > 0){
      html += `<div class="consumo-section">
        <h3>Consumo de Energia</h3>
        <table>
          <thead>
            <tr>
              <th>Período</th>
              <th>Valor</th>
              <th>Custo (€)</th>
            </tr>
          </thead>
          <tbody>`;
      
      data.energia.forEach(c=>{
        html += `<tr>
          <td>${c.periodo}</td>
          <td>${c.valor} ${c.unidade}</td>
          <td>${c.custo}</td>
        </tr>`;
      });
      
      html += `</tbody>
        </table>
      </div>`;
    }
    
    // Gás
    if(data.gas.length > 0){
      html += `<div class="consumo-section">
        <h3>Consumo de Gás</h3>
        <table>
          <thead>
            <tr>
              <th>Período</th>
              <th>Valor</th>
              <th>Custo (€)</th>
            </tr>
          </thead>
          <tbody>`;
      
      data.gas.forEach(c=>{
        html += `<tr>
          <td>${c.periodo}</td>
          <td>${c.valor} ${c.unidade}</td>
          <td>${c.custo}</td>
        </tr>`;
      });
      
      html += `</tbody>
        </table>
      </div>`;
    }
    
    html += '</div>';
    consumosDiv.innerHTML = html;
  });
}

function adicionarMarcador(){
  const lat = parseFloat(document.getElementById("latitude").value);
  const lng = parseFloat(document.getElementById("longitude").value);
  if(isNaN(lat) || isNaN(lng)){
    alert("Por favor, insira valores válidos para latitude e longitude.");
    return;
  }
  fetch(`/get_certificado?lat=${lat}&lng=${lng}`).then(r=>r.json()).then(casa=>{
    if(casa.latitude && casa.longitude){
      const cor = cores[casa.certificado.trim()] || cores[''];
      const icon = criarIcone(cor);
      limparMarkers();
      const marker = L.marker([casa.latitude, casa.longitude], {icon}).addTo(map);
      let texto = `<strong>${casa.morada}</strong><br>${casa.descricao}<br>
                   Latitude: ${casa.latitude.toFixed(5)}<br>
                   Longitude: ${casa.longitude.toFixed(5)}<br>
                   Certificado: <strong>${casa.certificado}</strong>`;
      if(casa.proprietario) texto += `<br><em>Proprietário: ${casa.proprietario}</em>`;
      marker.bindPopup(texto).openPopup();
      map.setView([casa.latitude, casa.longitude], 16);

      if({{ 'true' if session.get('logado') else 'false' }}) {
        carregarConsumos(casa.id || "");
      }
      markers = [marker];
    } else {
      alert('Casa não encontrada para as coordenadas dadas.');
    }
  });
}

function filtrarPorClasse() {
  const classeSelecionada = document.getElementById("filtroClasse").value;
  fetch("/todas_casas").then(r=>r.json()).then(data=>{
    limparMarkers();
    data.forEach(casa=>{
      if (!classeSelecionada || casa.certificado.trim() === classeSelecionada) {
        const cor = cores[casa.certificado.trim()] || cores[''];
        const icon = criarIcone(cor);
        const marker = L.marker([casa.latitude, casa.longitude], {icon}).addTo(map);
        let texto = `<strong>${casa.morada}</strong><br>${casa.descricao}<br>
                     Latitude: ${casa.latitude.toFixed(5)}<br>
                     Longitude: ${casa.longitude.toFixed(5)}<br>
                     Certificado: <strong>${casa.certificado}</strong>`;
        if (casa.proprietario) texto += `<br><em>Proprietário: ${casa.proprietario}</em>`;
        marker.bindPopup(texto);
        marker.on('click', () => {
          marker.openPopup();
          if({{ 'true' if session.get('logado') else 'false' }}) {
            carregarConsumos(casa.id);
          }
        });
        markers.push(marker);
      }
    });
  });
}

function limparPesquisa(){
  document.getElementById("latitude").value = "";
  document.getElementById("longitude").value = "";
  carregarCasas();
  map.setView([41.1578, -8.6291], 12); 
  document.getElementById("consumos").innerHTML = "";  
}

window.onload = function(){
  carregarCasas();

  const msg = document.getElementById("mensagem-alert");
  if(msg){
    setTimeout(() => {
      msg.style.opacity = "0";
      setTimeout(() => { msg.remove(); }, 800);
    }, 3000);
  }
}
</script>

</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML, session=session, mensagem=session.pop('mensagem', ''), logado=session.get('logado', False))

@app.route("/verifica_senha", methods=["POST"])
def verifica_senha():
    dados = request.get_json()
    senha = dados.get("senha", "")
    if senha == "adming3":
        session["logado"] = True
        session["mensagem"] = "Bem-vindo à Área Privada!"
        return jsonify(ok=True)
    else:
        return jsonify(ok=False)

@app.route("/logout")
def logout():
    session.clear()
    session["mensagem"] = "Sessão encerrada com sucesso."
    return redirect("/")

@app.route("/todas_casas")
def todas_casas():
    if not folha_casa:
        return jsonify([])
    dados = folha_casa.get_all_records()
    casas = []
    for d in dados:
        casas.append({
            'id': d.get('ID', ''),
            'descricao': d.get('Descrição', ''),
            'morada': d.get('Morada', ''),
            'latitude': float(d.get('Latitude', 0)),
            'longitude': float(d.get('Longitude', 0)),
            'certificado': d.get('Certificado Energético', '').strip(),
            'proprietario': d.get('Proprietário', '') if session.get('logado') else ''
        })
    return jsonify(casas)

@app.route("/get_certificado")
def get_certificado():
    if not folha_casa:
        return jsonify({})
    lat_c = float(request.args.get("lat", "0"))
    lng_c = float(request.args.get("lng", "0"))
    dados = folha_casa.get_all_records()
    for d in dados:
        try:
            lat = float(d.get('Latitude', 0))
            lng = float(d.get('Longitude', 0))
        except:
            continue
        if abs(lat - lat_c) < 0.0002 and abs(lng - lng_c) < 0.0002:
            return jsonify({
                'latitude': lat,
                'longitude': lng,
                'descricao': d.get('Descrição', ''),
                'morada': d.get('Morada', ''),
                'certificado': d.get('Certificado Energético', '').strip(),
                'proprietario': d.get('Proprietário', '') if session.get('logado') else '',
                'id': d.get('ID', '')
            })
    return jsonify({})

@app.route("/consumos")
def consumos():
    if not folha_consumo:
        return jsonify({'agua': [], 'energia': [], 'gas': []})
    id_casa = request.args.get("id")
    if not id_casa:
        return jsonify({'agua': [], 'energia': [], 'gas': []})
    
    dados = folha_consumo.get_all_records()
    
    # Separar consumos por tipo
    agua = []
    energia = []
    gas = []
    
    for d in dados:
        if str(d.get('ID Casa', '')) == str(id_casa):
            consumo = {
                'tipo': d.get('Tipo Consumo', ''),
                'periodo': d.get('Período', ''),
                'valor': d.get('Valor', ''),
                'unidade': d.get('Unidade', ''),
                'custo': d.get('Custo (€)', '')
            }
            tipo = consumo['tipo'].lower()
            if 'água' in tipo or 'agua' in tipo:
                agua.append(consumo)
            elif 'energia' in tipo:
                energia.append(consumo)
            elif 'gás' in tipo or 'gas' in tipo:
                gas.append(consumo)
    
    return jsonify({
        'agua': agua,
        'energia': energia,
        'gas': gas
    })

if __name__ == "__main__":
    app.run(debug=True, port=5000)
