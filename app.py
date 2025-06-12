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
      color:red; font-weight:bold; text-align:center;
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
    <div class="alert">{{ mensagem }}</div>
  {% endif %}
  <div id="form-coords">
    <input type="number" id="latitude" step="any" placeholder="Latitude"/>
    <input type="number" id="longitude" step="any" placeholder="Longitude"/>
    <button onclick="adicionarMarcador()">Mostrar no Mapa</button>
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
  const svg = <svg xmlns="http://www.w3.org/2000/svg" width="32" height="45" viewBox="0 0 32 45">
    <path fill="#${cor}" stroke="black" stroke-width="2" d="M16,1 C24.3,1 31,7.7 31,16 C31,27 16,44 16,44 C16,44 1,27 1,16 C1,7.7 7.7,1 16,1 Z"/>
  </svg>;
  return L.divIcon({html: svg, iconSize:[32,45], iconAnchor:[16,44], popupAnchor:[0,-40], className:''});
}

fetch('/todas_casas').then(r=>r.json()).then(casas => {
  casas.forEach(c => {
    const cor = cores[c.certificado] || cores[''];
    const icon = criarIcone(cor);
    const marker = L.marker([c.latitude, c.longitude], {icon}).addTo(map);
    let texto = <strong>${c.morada}</strong><br>${c.descricao}<br>
                 Latitude: ${c.latitude.toFixed(5)}<br>
                 Longitude: ${c.longitude.toFixed(5)}<br>
                 Certificado: <strong>${c.certificado}</strong>;
    if (c.proprietario) texto += <br><em>Proprietário: ${c.proprietario}</em>;
    marker.bindPopup(texto);
  });
});

function adicionarMarcador(){
  const lat = parseFloat(document.getElementById('latitude').value);
  const lng = parseFloat(document.getElementById('longitude').value);
  if(isNaN(lat)||isNaN(lng)){alert('Valores inválidos');return;}
  fetch(/get_certificado?lat=${lat}&lng=${lng}).then(r=>r.json()).then(c=>{
    if(!c.latitude){alert('Casa não encontrada'); return;}
    const cor = cores[c.certificado]||cores[''];
    const icon = criarIcone(cor);
    const mark = L.marker([c.latitude,c.longitude],{icon}).addTo(map);
    let texto = <strong>${c.morada}</strong><br>${c.descricao}<br>
                 Latitude: ${c.latitude.toFixed(5)}<br>
                 Longitude: ${c.longitude.toFixed(5)}<br>
                 Certificado: <strong>${c.certificado}</strong>;
    if (c.proprietario) texto += <br><em>Proprietário: ${c.proprietario}</em>;
    mark.bindPopup(texto).openPopup();
    map.setView([c.latitude,c.longitude],16);
  }).catch(_=>alert('Erro ao buscar casa'));
}
</script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML, session=session, mensagem=session.pop('mensagem', ''))

@app.route('/verifica_senha', methods=['POST'])
def verifica_senha():
    senha = request.json.get('senha')
    if senha == 'Adming3':
        session['logado'] = True
        return jsonify({'ok': True})
    return jsonify({'ok': False})

@app.route('/logout')
def logout():
    session.clear()
    session['messagem'] = 'Logout realizado com sucesso.'
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
o link do google shets:
1ºhttps://docs.google.com/spreadsheets/d/1SKveqiaBaYqyQ5JadM59JKQhd__jodFZfjl78KUGa9w/edit?gid=0#gid=0

2ºDados Consumos: https://docs.google.com/spreadsheets/d/1SKveqiaBaYqyQ5JadM59JKQhd__jodFZfjl78KUGa9w/edit?gid=634466147#gid=634466147

quero olgo do tipo mas baseado no meu tema: lembrando so aparece depois de fazer o login:
AVISO: nao mecher no layout que fiz, e nao mecher nada além depois do login, antes do login nao é para mecher, ok?
from flask import Flask, render_template, request, session, redirect, url_for 
import gspread
import os
import json
from google.oauth2.service_account import Credentials

app = Flask(__name__)
app.secret_key = 'app_secret_key'

SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly"
]

credenciais_json = json.loads(os.environ.get('GOOGLE_CREDENTIALS'))
credenciais = Credentials.from_service_account_info(credenciais_json)
credenciais = credenciais.with_scopes([
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly"
])

cliente = gspread.authorize(credenciais)
ID_SHEET = '1FsDLfIjmcBC8WQGUZ3Fg6VTpr1dtlOeEA8uct5r4LX0'

def obter_dados(nome_aba):
    try:
        sheet = cliente.open_by_key(ID_SHEET)
        aba = sheet.worksheet(nome_aba)
        return aba.get_all_records()
    except Exception as e:
        print(f"Erro ao obter dados: {e}")
        return []

def paginar(dados, por_pagina=10):
    return [dados[i:i+por_pagina] for i in range(0, len(dados), por_pagina)] if dados else []

@app.route('/', methods=['GET', 'POST'])
def index():
    error = None
    if request.method == 'POST':
        if request.form.get('password') == 'password':
            session['authenticated'] = True
            return redirect(url_for('index'))
        else:
            error = 'Password incorreta! Tente novamente.'

    # Obter parâmetros de paginação
    params = {
        'veiculos': int(request.args.get('page_veiculos', 1)),
        'alugueres': int(request.args.get('page_alugueres', 1)),
        'clientes': int(request.args.get('page_clientes', 1)),
        'stands': int(request.args.get('page_stands', 1))
    }

    # Obter e paginar dados
    dados = {
        'veiculos': paginar(obter_dados('Veiculos')),
        'alugueres': paginar(obter_dados('Alugueres')),
        'clientes': paginar(obter_dados('Clientes')) if session.get('authenticated') else [],
        'stands': paginar(obter_dados('Stands')) if session.get('authenticated') else []
    }

    contexto = {
        'authenticated': session.get('authenticated', False),
        'error': error,
        'params': params,
        'paginas': {
            tabela: {
                'atual': params[tabela],
                'total': len(dados[tabela]) if dados[tabela] else 0
            } for tabela in ['veiculos', 'alugueres', 'clientes', 'stands']
        }
    }

    for tabela in dados:
        contexto[tabela] = dados[tabela][params[tabela]-1] if dados[tabela] and 1 <= params[tabela] <= len(dados[tabela]) else []

    # Para o mapa dos stands:
    veiculos_lista = obter_dados('Veiculos')
    stands_lista = obter_dados('Stands')
    veiculos_por_stand = {}
    for veiculo in veiculos_lista:
        stand_nome = veiculo.get('Stand', '')
        matricula = veiculo.get('Matrícula', '') or veiculo.get('Matricula', '')
        if stand_nome:
            if stand_nome not in veiculos_por_stand:
                veiculos_por_stand[stand_nome] = []
            veiculos_por_stand[stand_nome].append(matricula)
    stands_mapa = []
    for stand in stands_lista:
        if stand.get('Latitude') and stand.get('Longitude'):
            stands_mapa.append({
                'Nome': stand.get('Stand', ''),
                'Latitude': stand.get('Latitude'),
                'Longitude': stand.get('Longitude'),
                'Matriculas': veiculos_por_stand.get(stand.get('Stand', ''), [])
            })
    contexto['stands_mapa'] = stands_mapa

    return render_template('index.html', **contexto)

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('authenticated', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
