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
    folha_consumos = planilha.worksheet("Dados Consumos")
except Exception as e:
    print("Erro init Google Sheets:", e)
    folha_casa = None
    folha_consumos = None

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

/* Modal login */
#loginModal {
  display:none; position:fixed; top:0; left:0; width:100%; height:100%;
  background-color:rgba(0,0,0,0.5); z-index:1000;
  justify-content:center; align-items:center;
}
#loginModalContent {
  background:white; padding:30px; border-radius:10px;
  box-shadow:0 0 20px rgba(0,0,0,0.2); text-align:center;
}

/* Consumos - estilo NASA */
#consumos-container {
  margin-top: 30px;
}
.casa-card {
  background: linear-gradient(145deg, #0b3d91, #144fbc);
  color: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 0 15px rgba(11, 61, 145, 0.8);
  margin-bottom: 30px;
}
.casa-header {
  font-size: 1.4rem;
  font-weight: 700;
  margin-bottom: 8px;
  border-bottom: 2px solid #8ab4f8;
  padding-bottom: 4px;
}
.proprietario {
  font-style: italic;
  font-weight: 600;
  opacity: 0.8;
  margin-bottom: 15px;
}
.consumos-list {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}
.consumo-item {
  background: rgba(255, 255, 255, 0.15);
  border-radius: 10px;
  flex: 1 1 150px;
  min-width: 150px;
  padding: 15px 20px;
  box-shadow: inset 0 0 10px rgba(255,255,255,0.2);
  transition: transform 0.3s ease;
}
.consumo-item:hover {
  transform: scale(1.05);
  background: rgba(255, 255, 255, 0.3);
}
.consumo-tipo {
  font-weight: 700;
  font-size: 1.1rem;
  margin-bottom: 6px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.consumo-valor {
  font-size: 1.2rem;
  font-weight: 600;
}
.consumo-custo {
  margin-top: 6px;
  font-size: 1rem;
  font-weight: 500;
  opacity: 0.9;
  text-align: right;
  color: #d1d1ff;
}

/* Ícones simples inline SVG para tipos */
.icon-agua {
  width: 20px; height: 20px;
  fill: #66ccff;
}
.icon-energia {
  width: 20px; height: 20px;
  fill: #ffd700;
}
.icon-gas {
  width: 20px; height: 20px;
  fill: #ff704d;
}

@media (max-width: 600px) {
  #map { height: 300px; }
  .consumos-list {
    flex-direction: column;
  }
  .consumo-item {
    min-width: 100%;
  }
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

  {% if session.get('logado') %}
  <section id="consumos-container">
    <h2 style="color:#0077cc; font-weight:700; margin-bottom: 1rem;">Consumos das Casas</h2>
    {% for casa in consumos_agrupados %}
    <div class="casa-card">
      <div class="casa-header">{{ casa.morada }} (ID: {{ casa.id }})</div>
      <div class="proprietario">Proprietário: {{ casa.proprietario }}</div>
      <div class="consumos-list">
        {% for consumo in casa.consumos %}
        <div class="consumo-item">
          <div class="consumo-tipo">
            {% if consumo.tipo.lower() == 'água' %}
              <svg class="icon-agua" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg"><path d="M32 2C19 20 10 34 10 44a22 22 0 0044 0c0-10-9-24-22-42z"/></svg>
            {% elif consumo.tipo.lower() == 'energia' %}
              <svg class="icon-energia" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg"><path d="M32 2L12 42h16l-6 20 26-40H38z"/></svg>
            {% elif consumo.tipo.lower() == 'gás' %}
              <svg class="icon-gas" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg"><circle cx="32" cy="32" r="30"/></svg>
            {% else %}
              <span>{{ consumo.tipo }}</span>
            {% endif %}
            {{ consumo.tipo }}
          </div>
          <div>Período: {{ consumo.periodo }}</div>
          <div class="consumo-valor">{{ consumo.valor }} {{ consumo.unidade }}</div>
          <div class="consumo-custo">Custo: € {{ '%.2f'|format(consumo.custo) }}</div>
        </div>
        {% endfor %}
      </div>
    </div>
    {% endfor %}
  </section>
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
  Este sistema é fictício e destina-se exclusivamente a fins académicos.
</footer>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
  let map = L.map('map').setView([38.736946, -9.142685], 13);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{
    maxZoom:19, attribution:'© OpenStreetMap contributors'
  }).addTo(map);

  // Casas do Google Sheets (Dados Casa)
  let casas = {{ casas_json|safe }};
  let marcadores = [];

  casas.forEach(casa => {
    let marker = L.marker([parseFloat(casa.Latitude), parseFloat(casa.Longitude)]).addTo(map);
    marker.bindPopup(`<b>${casa.Descrição}</b><br>${casa.Morada}<br><b>Certificado:</b> ${casa['Certificado Energético']}`);
    marcadores.push(marker);
  });

  function adicionarMarcador(){
    let lat = parseFloat(document.getElementById('latitude').value);
    let lon = parseFloat(document.getElementById('longitude').value);
    if(isNaN(lat) || isNaN(lon)){
      alert('Por favor, insira coordenadas válidas!');
      return;
    }
    let marker = L.marker([lat, lon]).addTo(map);
    map.setView([lat, lon], 16);
  }

  // Login modal control
  function abrirLogin(){
    document.getElementById('loginModal').style.display = 'flex';
    document.getElementById('senhaInput').value = '';
    document.getElementById('erroSenha').textContent = '';
  }
  function fecharLogin(){
    document.getElementById('loginModal').style.display = 'none';
  }

  async function enviarSenha(){
    const senha = document.getElementById('senhaInput').value.trim();
    if(!senha){
      document.getElementById('erroSenha').textContent = 'Senha não pode ser vazia.';
      return;
    }
    const resp = await fetch('/login', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({senha})
    });
    const data = await resp.json();
    if(data.sucesso){
      window.location.reload();
    } else {
      document.getElementById('erroSenha').textContent = data.mensagem || 'Senha incorreta.';
    }
  }

  function confirmarLogout(){
    if(confirm('Tem certeza que deseja sair da Área Privada?')){
      fetch('/logout').then(() => {
        alert('Logout efetuado com sucesso.');
        window.location.reload();
      });
    }
  }
</script>
</body>
</html>
"""

def ler_casas():
    if not folha_casa:
        return []
    dados = folha_casa.get_all_records()
    # renomear campos para chave única mais fácil
    casas = []
    for d in dados:
        casas.append({
            'id': str(d.get('ID Casa') or d.get('ID') or ''),
            'Descrição': d.get('Descrição') or '',
            'Morada': d.get('Morada') or '',
            'Latitude': d.get('Latitude') or 0,
            'Longitude': d.get('Longitude') or 0,
            'Proprietário': d.get('Proprietário') or '',
            'Certificado Energético': d.get('Certificado Energético') or '',
        })
    return casas

def ler_consumos():
    if not folha_consumos:
        return []
    dados = folha_consumos.get_all_records()
    consumos = []
    for d in dados:
        consumos.append({
            'id': str(d.get('ID Casa') or ''),
            'tipo': d.get('Tipo Consumo') or '',
            'periodo': d.get('Período') or '',
            'valor': d.get('Valor') or 0,
            'unidade': d.get('Unidade') or '',
            'custo': float(d.get('Custo (€)') or 0)
        })
    return consumos

@app.route('/')
def index():
    casas = ler_casas()
    # Passar casas para JS para criar marcadores
    casas_json = json.dumps(casas)
    mensagem = session.pop('mensagem', None)

    consumos_agrupados = []
    if session.get('logado'):
        consumos = ler_consumos()
        # Agrupar consumos por casa
        dicionario_casas = {c['id']: c for c in casas}
        casas_com_consumos = {}
        for c in consumos:
            casaid = c['id']
            if casaid not in casas_com_consumos:
                casa_info = dicionario_casas.get(casaid, {})
                casas_com_consumos[casaid] = {
                    'id': casaid,
                    'morada': casa_info.get('Morada', 'Morada desconhecida'),
                    'proprietario': casa_info.get('Proprietário', 'Proprietário desconhecido'),
                    'consumos': []
                }
            casas_com_consumos[casaid]['consumos'].append(c)

        consumos_agrupados = list(casas_com_consumos.values())

    return render_template_string(HTML,
                                  casas_json=casas_json,
                                  mensagem=mensagem,
                                  consumos_agrupados=consumos_agrupados)

@app.route('/login', methods=['POST'])
def login():
    dados = request.get_json()
    senha = dados.get('senha', '')
    if senha == 'Adming3':
        session['logado'] = True
        return jsonify({"sucesso": True})
    else:
        return jsonify({"sucesso": False, "mensagem": "Senha incorreta."})

@app.route('/logout')
def logout():
    session.pop('logado', None)
    session['mensagem'] = 'Logout efetuado com sucesso.'
    return redirect('/')

if __name__ == "__main__":
    app.run(debug=True)
