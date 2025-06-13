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
    input[type="number"], input[type="text"], input[type="password"], select {
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
      color:green; font-weight:bold; text-align:center;
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
    @media (max-width:600px) {
      header {flex-direction:column; align-items:flex-start; gap:10px; padding:1rem;}
      #header-right {width:100%; justify-content:space-between;}
      h1 {font-size:1.5em;}
      #form-coords {display:flex; flex-direction:column; align-items:center;}
      input, button, select {width:90%; margin:6px 0;}
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
  </div>
  
  <div id="filtro-certificado" style="text-align:center; margin-bottom:15px;">
    <label for="certificadoFiltro">Filtrar certificados Energéticos: </label>
    <select id="certificadoFiltro" onchange="filtrarPorCertificado()">
      <option value="">-- Todos --</option>
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
      <option value="">Sem Certificado</option>
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
  document.getElementById("erroSenha").textContent = "";
  document.getElementById("senhaInput").value = "";
}
function enviarSenha(){
  let senha = document.getElementById("senhaInput").value.trim();
  if(senha.length === 0){
    document.getElementById("erroSenha").textContent = "Por favor, digite a senha.";
    return;
  }
  fetch('/login', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({senha: senha})
  })
  .then(r => r.json())
  .then(resp => {
    if(resp.sucesso){
      window.location.reload();
    } else {
      document.getElementById("erroSenha").textContent = "Senha incorreta!";
    }
  });
}

const cores = {
  "A+": "#008000", "A": "#00A000", "A-": "#40B040",
  "B+": "#A2C52D", "B": "#ADFF2F", "B-": "#C1E18F",
  "C+": "#FFD700", "C": "#FDD017", "C-": "#F0E68C",
  "D+": "#FF8C00", "D": "#FF7F00", "D-": "#FFA500",
  "E+": "#FF4500", "E": "#FF6347", "E-": "#FF7F50",
  "F+": "#FF0000", "F": "#CD5C5C", "F-": "#B22222",
  "G+": "#8B0000", "G": "#800000", "G-": "#660000",
  "": "#777777"  // Sem certificado
};

let map = L.map('map').setView([41.1578, -8.6291], 12);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{
  attribution: '© OpenStreetMap contributors'
}).addTo(map);

let markers = [];
let todasCasasCache = [];

function criarIcone(cor){
  return L.divIcon({
    className: "custom-div-icon",
    html: `<div style="background-color:${cor}; width:18px; height:18px; border-radius:50%; border:2px solid white;"></div>`,
    iconSize: [18, 18],
    iconAnchor: [9, 9]
  });
}

function limparMarkers(){
  markers.forEach(m => map.removeLayer(m));
  markers = [];
}

function mostrarCasasNoMapa(filtroCertificado = ""){
  limparMarkers();
  const filtro = filtroCertificado.trim();
  const casasFiltradas = filtro
    ? todasCasasCache.filter(casa => casa.certificado === filtro)
    : todasCasasCache;

  casasFiltradas.forEach(casa => {
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
      {% if session.get('logado') %}
      carregarConsumos(casa.id);
      {% endif %}
    });
    markers.push(marker);
  });

  if(markers.length > 0){
    const group = new L.featureGroup(markers);
    map.fitBounds(group.getBounds().pad(0.1));
  }
}

function carregarCasas(filtroCertificado = ""){
  fetch("/todas_casas").then(r => r.json()).then(data => {
    todasCasasCache = data;
    mostrarCasasNoMapa(filtroCertificado);
  });
}

function filtrarPorCertificado(){
  const select = document.getElementById("certificadoFiltro");
  const valor = select.value;
  mostrarCasasNoMapa(valor);
  document.getElementById("consumos").innerHTML = "";
}

function limparPesquisa(){
  document.getElementById("latitude").value = "";
  document.getElementById("longitude").value = "";
  document.getElementById("certificadoFiltro").value = "";
  carregarCasas();
  map.setView([41.1578, -8.6291], 12);
  document.getElementById("consumos").innerHTML = "";
}

function adicionarMarcador(){
  const lat = parseFloat(document.getElementById("latitude").value);
  const lng = parseFloat(document.getElementById("longitude").value);
  if(isNaN(lat) || isNaN(lng)){
    alert("Por favor, insira valores válidos para latitude e longitude.");
    return;
  }
  limparMarkers();
  const marker = L.marker([lat, lng]).addTo(map);
  markers.push(marker);
  map.setView([lat, lng], 16);
  document.getElementById("consumos").innerHTML = "";
}

function carregarConsumos(idCasa){
  fetch(`/consumos/${idCasa}`).then(r => r.json()).then(data => {
    if(!data || data.length === 0){
      document.getElementById("consumos").innerHTML = "<p>Nenhum consumo disponível para esta casa.</p>";
      return;
    }
    let html = `<h3>Consumos da Casa ID: ${idCasa}</h3><table>
                <thead><tr><th>Tipo</th><th>Período</th><th>Valor</th><th>Custo (€)</th></tr></thead><tbody>`;
    data.forEach(c => {
      html += `<tr>
        <td>${c.tipo}</td>
        <td>${c.periodo}</td>
        <td>${c.valor} ${c.unidade}</td>
        <td>€${c.custo.toFixed(2)}</td>
      </tr>`;
    });
    html += "</tbody></table>";
    document.getElementById("consumos").innerHTML = html;
  });
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
};
</script>

</body>
</html>
"""

@app.route("/")
def index():
    mensagem = session.pop("mensagem", None)
    return render_template_string(HTML, mensagem=mensagem, session=session)

@app.route("/todas_casas")
def todas_casas():
    if folha_casa is None:
        return jsonify([])

    try:
        dados = folha_casa.get_all_records()
        casas = []
        for linha in dados:
            casas.append({
                "id": linha.get("ID Casa", ""),
                "descricao": linha.get("Descrição", ""),
                "morada": linha.get("Morada", ""),
                "latitude": float(linha.get("Latitude", 0)),
                "longitude": float(linha.get("Longitude", 0)),
                "certificado": linha.get("Certificado Energético", "").strip(),
                "proprietario": linha.get("Proprietário", "").strip()
            })
        return jsonify(casas)
    except Exception as e:
        print("Erro ao buscar casas:", e)
        return jsonify([])

@app.route("/consumos/<id_casa>")
def consumos(id_casa):
    if folha_consumo is None:
        return jsonify([])

    try:
        dados = folha_consumo.get_all_records()
        consumos = []
        for linha in dados:
            if str(linha.get("ID Casa", "")) == str(id_casa):
                consumos.append({
                    "tipo": linha.get("Tipo Consumo", ""),
                    "periodo": linha.get("Período", ""),
                    "valor": linha.get("Valor", ""),
                    "unidade": linha.get("Unidade", ""),
                    "custo": float(linha.get("Custo (€)", 0) or 0)
                })
        return jsonify(consumos)
    except Exception as e:
        print("Erro ao buscar consumos:", e)
        return jsonify([])

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    senha = data.get("senha", "")
    if senha == "senha123":  # troque para sua senha real
        session["logado"] = True
        session["mensagem"] = "Login efetuado com sucesso!"
        return jsonify({"sucesso": True})
    else:
        return jsonify({"sucesso": False})

@app.route("/logout")
def logout():
    session.pop("logado", None)
    session["mensagem"] = "Logout efetuado com sucesso!"
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
