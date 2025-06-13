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
  document.getElementById("senhaInput").value = "";
  document.getElementById("erroSenha").innerText = "";
  document.getElementById("senhaInput").focus();
}
function fecharLogin(){
  document.getElementById("loginModal").style.display = "none";
}
function enviarSenha(){
  const senha = document.getElementById("senhaInput").value.trim();
  if(!senha) {
    document.getElementById("erroSenha").innerText = "Por favor, digite a senha.";
    return;
  }
  fetch('/verifica_senha', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ senha })
  }).then(res => res.json())
  .then(data => {
    if(data.ok){
      location.reload();
    } else {
      document.getElementById("erroSenha").innerText = "Senha incorreta.";
    }
  });
}

const map = L.map('map').setView([-23.517415, -46.422033], 14);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  attribution: '&copy; OpenStreetMap contributors'
}).addTo(map);

let markers = [];
let casasData = [];
const logado = {{ 'true' if session.get('logado') else 'false' }};

function corCertificado(cert){
  switch(cert){
    case "A+": return "darkgreen";
    case "A": return "green";
    case "A-": return "#228B22";
    case "B+": return "#32CD32";
    case "B": return "#66CDAA";
    case "B-": return "#7FFFD4";
    case "C+": return "#FFFF00";
    case "C": return "#FFD700";
    case "C-": return "#FFA500";
    case "D+": return "#FF8C00";
    case "D": return "#FF7F50";
    case "D-": return "#FF6347";
    case "E+": return "#FF4500";
    case "E": return "#FF0000";
    case "E-": return "#DC143C";
    case "F+": return "#B22222";
    case "F": return "#8B0000";
    case "F-": return "#800000";
    case "G+": return "#4B0082";
    case "G": return "#2F4F4F";
    case "G-": return "#000000";
    default: return "#555555";
  }
}

function carregaCasas(filtro=''){
  fetch('/todas_casas')
  .then(res => res.json())
  .then(data => {
    casasData = data;
    limparMarcadores();
    let contagem = 0;
    for(let casa of casasData){
      if(filtro && casa.certificado !== filtro) continue;
      const cor = corCertificado(casa.certificado);
      const marker = L.circleMarker([casa.latitude, casa.longitude], {
        radius: 8,
        color: cor,
        fillColor: cor,
        fillOpacity: 0.9,
        weight: 2,
        className: 'markerCertificado'
      }).addTo(map);
      marker.bindPopup(`<b>${casa.descricao}</b><br>${casa.morada}<br>Certificado: ${casa.certificado}`);
      marker.casaId = casa.id;
      marker.on('click', () => {
        if(logado){
          mostrarConsumos(marker.casaId);
        } else {
          alert("Para ver os consumos, faça login na Área Privada.");
        }
      });
      markers.push(marker);
      contagem++;
    }
    if(contagem === 0 && filtro) alert("Nenhuma casa com este certificado.");
  });
}

function limparMarcadores(){
  for(let m of markers){
    map.removeLayer(m);
  }
  markers = [];
}

function filtrarPorClasse(){
  const filtro = document.getElementById("filtroClasse").value;
  carregaCasas(filtro);
  limparTabelaConsumos();
}

function adicionarMarcador(){
  const lat = parseFloat(document.getElementById("latitude").value);
  const lng = parseFloat(document.getElementById("longitude").value);
  if(isNaN(lat) || isNaN(lng)) {
    alert("Informe coordenadas válidas.");
    return;
  }
  map.setView([lat, lng], 17);
  limparMarcadores();
  const marker = L.marker([lat, lng]).addTo(map);
  marker.bindPopup("Coordenadas selecionadas").openPopup();
  markers.push(marker);
  limparTabelaConsumos();
}

function limparPesquisa(){
  document.getElementById("latitude").value = "";
  document.getElementById("longitude").value = "";
  document.getElementById("filtroClasse").value = "";
  limparMarcadores();
  carregaCasas();
  limparTabelaConsumos();
}

function limparTabelaConsumos(){
  const div = document.getElementById("consumos");
  if(div) div.innerHTML = "";
}

function mostrarConsumos(idCasa){
  fetch(`/consumos?id=${idCasa}`)
  .then(res => res.json())
  .then(data => {
    const div = document.getElementById("consumos");
    if(!div) return;
    if(data.length === 0){
      div.innerHTML = "<p>Não há consumos para esta casa.</p>";
      return;
    }
    // Agrupar por tipo
    const agrupados = {};
    for(const c of data){
      if(!agrupados[c.tipo]) agrupados[c.tipo] = [];
      agrupados[c.tipo].push(c);
    }

    let html = `<h2>Consumos da Casa ${idCasa}</h2>`;
    for(const tipo in agrupados){
      html += `<h3>${tipo}</h3>`;
      html += `<table><thead><tr><th>Período</th><th>Valor</th><th>Custo (€)</th></tr></thead><tbody>`;
      for(const reg of agrupados[tipo]){
        html += `<tr>
          <td>${reg.periodo}</td>
          <td>${reg.valor} ${reg.unidade}</td>
          <td>${reg.custo}</td>
        </tr>`;
      }
      html += "</tbody></table>";
    }
    div.innerHTML = html;
  });
}

document.addEventListener("DOMContentLoaded", () => {
  carregaCasas();
  if(document.getElementById("mensagem-alert")){
    setTimeout(() => {
      document.getElementById("mensagem-alert").style.opacity = 0;
    }, 4000);
  }
});
</script>
</body>
</html>
"""

def get_houses():
    if not folha_casa:
        return []
    try:
        dados = folha_casa.get_all_records()
    except Exception as e:
        print("Erro ao buscar casas:", e)
        return []
    casas = []
    for d in dados:
        try:
            casas.append({
                "id": str(d.get("ID Casa", "")).strip(),
                "morada": d.get("Morada", ""),
                "descricao": d.get("Descrição", ""),
                "latitude": float(d.get("Latitude", 0)),
                "longitude": float(d.get("Longitude", 0)),
                "certificado": d.get("Certificado Energético", "").strip(),
                "proprietario": d.get("Proprietário", "").strip(),
            })
        except Exception as e:
            print("Erro processar casa:", e)
    return casas

def get_consumos(id_casa):
    if not folha_consumo:
        return []
    try:
        dados = folha_consumo.get_all_records()
    except Exception as e:
        print("Erro ao buscar consumos:", e)
        return []
    consumos = []
    for d in dados:
        try:
            if str(d.get("ID Casa", "")).strip() == str(id_casa).strip():
                consumos.append({
                    "tipo": d.get("Tipo Consumo", ""),
                    "periodo": d.get("Período", ""),
                    "valor": d.get("Valor", ""),
                    "unidade": d.get("Unidade", ""),
                    "custo": d.get("Custo (€)", ""),
                })
        except Exception as e:
            print("Erro processar consumo:", e)
    return consumos

@app.route("/")
def index():
    mensagem = session.pop('mensagem', '') if 'mensagem' in session else ''
    return render_template_string(HTML, session=session, mensagem=mensagem)

@app.route("/todas_casas")
def todas_casas():
    casas = get_houses()
    return jsonify(casas)

@app.route("/consumos")
def consumos():
    id_casa = request.args.get("id", "")
    if not id_casa:
        return jsonify([])
    consumos = get_consumos(id_casa)
    return jsonify(consumos)

@app.route("/verifica_senha", methods=["POST"])
def verifica_senha():
    data = request.get_json()
    senha = data.get("senha", "")
    senha_correta = os.getenv("SENHA", "senha123")  # Senha padrão para testes
    if senha == senha_correta:
        session['logado'] = True
        return jsonify({"ok": True})
    else:
        return jsonify({"ok": False})

@app.route("/logout")
def logout():
    session.clear()
    session['mensagem'] = "Logout efetuado com sucesso!"
    return redirect("/")

if __name__ == "__main__":
    # Para rodar localmente
    app.run(debug=True, port=5000)
