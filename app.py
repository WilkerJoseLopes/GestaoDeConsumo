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
    html, body {margin:0; padding:0; height:100%}
    body {
      font-family:'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      display:flex; flex-direction:column; min-height:100vh;
      background-color:#f4f7f9; color:#333;
    }
    header {
      background-color:#0077cc; color:white;
      padding:1rem 2rem; display:flex;
      justify-content:space-between; align-items:center;
      flex-wrap:wrap;
    }
    header h1 {margin:0; font-weight:600; font-size:1.8rem;}
    header h1 a {color:white; text-decoration:none;}
    #header-right {display:flex; align-items:center; gap:20px; flex-wrap:wrap;}
    #header-right a, #header-right span {
      font-size:1rem; color:white; text-decoration:none; cursor:pointer;
    }
    #header-right a:hover {text-decoration:underline;}
    #logoutBtn {
      color: #ff4d4d; /* vermelho */
      font-weight: bold;
      cursor: pointer;
    }
    main {
      flex:1; padding:20px; max-width:960px; margin:0 auto;
      width:100%; display:flex; flex-direction:column; gap:20px;
    }
    #form-coords {text-align:center;}
    input[type="number"], input[type="text"], input[type="password"] {
      padding:10px; margin:8px; width:200px; max-width:90%;
      border-radius:6px; border:1px solid #ccc; box-sizing:border-box;
    }
    button {
      padding:10px 16px; border:none; border-radius:6px;
      background-color:#0077cc; color:white; cursor:pointer;
    }
    button:hover {background-color:#005fa3;}
    #map {
      height:500px; width:100%;
      border-radius:10px;
      box-shadow:0 0 12px rgba(0,0,0,0.15);
      background-color:lightgray;
    }
    footer {
      background-color:#222; color:#ccc;
      text-align:center; padding:15px 20px; font-size:0.9em;
      width:100%;
    }
    .alert {
      color:#0f0; font-weight:bold; text-align:center;
      opacity: 1;
      transition: opacity 0.5s ease-out;
    }
    #loginModal {
      display:none; position:fixed; top:0; left:0; width:100%; height:100%;
      background-color:rgba(0,0,0,0.5); z-index:1000;
      justify-content:center; align-items:center;
    }
    #loginModalContent {
      background:white; padding:30px; border-radius:10px;
      box-shadow:0 0 20px rgba(0,0,0,0.2); text-align:center;
      max-width:320px;
      width:90%;
    }
    #consumos {
      margin-top: 10px;
      background:#fff;
      border-radius:10px;
      padding:20px;
      box-shadow:0 0 10px rgba(0,0,0,0.1);
    }
    table {
      border-collapse: collapse;
      width: 100%;
    }
    th, td {
      border: 1px solid #ccc;
      padding: 8px;
      text-align: center;
    }
    th {
      background-color: #0077cc;
      color: white;
    }
    #passoAPasso {
      margin-bottom: 15px;
      font-size: 1rem;
      color: #0077cc;
      background: #e7f0ff;
      border-left: 5px solid #0077cc;
      padding: 10px 15px;
      border-radius: 6px;
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
      <span id="logoutBtn" onclick="confirmarLogout()">Logout</span>
    {% endif %}
  </div>
</header>

<main>
  {% if mensagem %}
    <div class="alert" id="msgLogout">{{ mensagem }}</div>
  {% endif %}
  <div id="form-coords">
    <input type="number" id="latitude" step="any" placeholder="Latitude"/>
    <input type="number" id="longitude" step="any" placeholder="Longitude"/>
    <button onclick="adicionarMarcador()">Mostrar no Mapa</button>
  </div>
  <div id="map"></div>

  {% if session.get('logado') %}
  <div id="consumos">
    <div id="passoAPasso">
      <strong>Passo a passo para ver consumos:</strong><br>
      1. Clique no marcador da casa no mapa.<br>
      2. Aguarde a tabela de consumos carregar abaixo do mapa.<br>
      3. Veja os detalhes de água, energia e gás.<br>
      4. Para outra casa, clique em outro marcador.<br>
    </div>
    <h2>Consumos da Casa Selecionada</h2>
    <p id="infoConsumo">Clique em um marcador para ver os consumos.</p>
    <table id="tabelaConsumos" style="display:none;">
      <thead>
        <tr>
          <th>Tipo Consumo</th>
          <th>Período</th>
          <th>Valor</th>
          <th>Custo (€)</th>
        </tr>
      </thead>
      <tbody id="corpoTabelaConsumos"></tbody>
    </table>
  </div>
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
  Este sistema é fictício e destina-se exclusivamente a fins académicos e demonstrativos.
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
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({senha})
  }).then(r=>r.json())
  .then(data=>{
    if(data.ok){
      window.location.reload();
    } else {
      document.getElementById("erroSenha").textContent = "Senha incorreta!";
    }
  });
}

// Faz sumir a mensagem de logout após 3 segundos
window.onload = function(){
  const msg = document.getElementById('msgLogout');
  if(msg){
    setTimeout(() => {
      msg.style.opacity = 0;
      setTimeout(() => { msg.remove(); }, 500);
    }, 3000);
  }
};

// INICIALIZA MAPA E MARCADORES
var map = L.map('map').setView([38.71667, -9.13989], 13);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{
  attribution:'&copy; OpenStreetMap contributors'
}).addTo(map);

var marcadores = [];

fetch('/todas_casas')
.then(r => r.json())
.then(casas => {
  casas.forEach(c => {
    const lat = parseFloat(c.latitude);
    const lng = parseFloat(c.longitude);
    if(isNaN(lat) || isNaN(lng)) return;
    const marker = L.marker([lat, lng]).addTo(map);

    // Mostrar popup diferente antes/depois do login
    let popupConteudo = `<b>${c.descricao}</b><br>${c.morada}<br>Latitude: ${lat.toFixed(5)}<br>Longitude: ${lng.toFixed(5)}<br>Certificado: ${c.certificado}`;
    {% raw %}
    if({{ 'true' if session.get('logado') else 'false' }}){
      popupConteudo += `<br><b>Proprietário: Proprietário</b>`;
    }
    {% endraw %}
    marker.bindPopup(popupConteudo);

    marker.casaId = c.id;
    marcadores.push(marker);

    marker.on('click', function(){
      {% raw %}
      if({{ 'true' if session.get('logado') else 'false' }}) {
        mostrarConsumos(this.casaId);
      }
      {% endraw %}
    });
  });
});

function adicionarMarcador(){
  const lat = parseFloat(document.getElementById("latitude").value);
  const lng = parseFloat(document.getElementById("longitude").value);
  if(isNaN(lat) || isNaN(lng)){
    alert("Por favor insira latitude e longitude válidas.");
    return;
  }
  map.setView([lat,lng],16);
  const marker = L.marker([lat,lng]).addTo(map);
  marker.bindPopup("Local inserido").openPopup();
}

function mostrarConsumos(idCasa){
  fetch('/consumos/' + idCasa)
  .then(r => r.json())
  .then(data => {
    const tabela = document.getElementById('tabelaConsumos');
    const corpo = document.getElementById('corpoTabelaConsumos');
    const info = document.getElementById('infoConsumo');
    if(data.length === 0){
      info.textContent = "Não há consumos para esta casa.";
      tabela.style.display = "none";
      return;
    }
    corpo.innerHTML = "";
    data.forEach(item => {
      const tr = document.createElement('tr');
      tr.innerHTML = `<td>${item.tipo}</td><td>${item.periodo}</td><td>${item.valor} ${item.unidade}</td><td>${item.custo.toFixed(2)}</td>`;
      corpo.appendChild(tr);
    });
    info.textContent = "";
    tabela.style.display = "table";
  });
}
</script>
</body>
</html>"""

def obter_casas():
    try:
        dados = folha_casa.get_all_records()
        casas = []
        for linha in dados:
            casas.append({
                'id': linha.get('ID', ''),
                'descricao': linha.get('Descrição', ''),
                'morada': linha.get('Morada', ''),
                'latitude': float(linha.get('Latitude', 0)),
                'longitude': float(linha.get('Longitude', 0)),
                'certificado': linha.get('Certificado Energético', '').strip()
            })
        return casas
    except Exception as e:
        print("Erro ao obter casas:", e)
        return []

def obter_consumos(id_casa):
    try:
        todos = folha_consumo.get_all_records()
        consumos = []
        for c in todos:
            if str(c.get('ID Casa')) == str(id_casa):
                consumos.append({
                    'tipo': c.get('Tipo Consumo', ''),
                    'periodo': c.get('Período', ''),
                    'valor': c.get('Valor', 0),
                    'unidade': c.get('Unidade', ''),
                    'custo': float(c.get('Custo (€)', 0))
                })
        return consumos
    except Exception as e:
        print("Erro ao obter consumos:", e)
        return []

@app.route('/')
def index():
    mensagem = session.pop('mensagem', None)
    return render_template_string(HTML, mensagem=mensagem, session=session)

@app.route('/todas_casas')
def todas_casas():
    casas = obter_casas()
    return jsonify(casas)

@app.route('/consumos/<id_casa>')
def consumos(id_casa):
    if not session.get('logado'):
        return jsonify([])
    dados = obter_consumos(id_casa)
    return jsonify(dados)

@app.route('/verifica_senha', methods=['POST'])
def verifica_senha():
    data = request.json
    senha = data.get('senha', '')
    senha_correta = "Adming3"
    if senha == senha_correta:
        session['logado'] = True
        session['usuario'] = 'Proprietário'
        return jsonify({'ok': True})
    else:
        return jsonify({'ok': False})

@app.route('/logout')
def logout():
    session.clear()
    session['mensagem'] = "Logout efetuado com sucesso!"
    return redirect('/')

if __name__ == "__main__":
    app.run(debug=True)
