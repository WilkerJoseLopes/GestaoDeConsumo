import os
import json
import gspread
from flask import Flask, render_template_string, request, jsonify, session
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
<head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Gestão de Consumo</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<style>
html, body {margin:0; padding:0; height:100%;}
body {
  font-family:'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  display:flex; flex-direction:column; min-height:100vh;
  background-color:#f4f7f9; color:#333;
}
header {
  background-color:#0077cc; color:white; padding:1rem 2rem;
  display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap;
}
header h1 {margin:0; font-weight:600; font-size:1.8rem;}
header h1 a {color:white; text-decoration:none;}
#header-right {
  display:flex; align-items:center; gap:20px; flex-wrap:wrap;
}
#header-right a, #header-right span {
  font-size:1rem; color:white; text-decoration:none; cursor:pointer;
}
#header-right a:hover {text-decoration:underline;}
main {
  flex:1; padding:20px; max-width:960px; margin:0 auto; width:100%;
  display:flex; flex-direction:column; gap:20px;
}
#form-coords {
  text-align:center;
  display:flex;
  justify-content:center;
  gap:10px;
  flex-wrap:wrap;
}
input[type="number"], input[type="text"], input[type="password"] {
  padding:10px; margin:8px 0; width:200px; max-width:90%;
  border-radius:6px; border:1px solid #ccc; box-sizing:border-box;
  transition: border-color 0.3s ease;
  font-size:1rem;
}
input.error {
  border-color: red !important;
  outline: none;
}
button {
  padding:10px 16px; border:none; border-radius:6px;
  background-color:#0077cc; color:white; cursor:pointer;
  font-size:1rem;
  min-width:120px;
  transition: background-color 0.3s ease;
}
button:disabled {
  background-color: #a0c4e3;
  cursor: not-allowed;
}
button:hover:not(:disabled) {
  background-color:#005fa3;
}
#map {
  height:500px; width:100%; border-radius:10px;
  box-shadow:0 0 12px rgba(0,0,0,0.15);
  background-color:lightgray;
  margin-top:10px;
}
footer {
  background-color:#222; color:#ccc; text-align:center;
  padding:15px 20px; font-size:0.9em; width:100%;
}
.alert {
  color:green;
  font-weight:bold;
  text-align:center;
  margin-top:5px;
  opacity: 1;
  transition: opacity 0.5s ease;
  user-select:none;
  min-height:1.2em;
}
.alert.error {
  color:red;
}
@media (max-width:600px) {
  header {
    flex-direction:column; align-items:flex-start; gap:10px; padding:1rem;
  }
  #header-right {
    width:100%; justify-content:space-between;
  }
  h1 {
    font-size:1.5em;
  }
  #form-coords {
    flex-direction: column;
    align-items: center;
  }
  input, button {
    width:90%;
    margin: 6px 0;
    min-width: unset;
  }
  #map {
    height:300px;
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
      <span id="abrir-login" style="cursor:pointer; color:#eee; text-decoration:underline;">Área Privada</span>
    {% else %}
      <span onclick="confirmarLogout()" style="cursor:pointer;">Logout</span>
    {% endif %}
  </div>
</header>
<main>

<div id="mensagem" class="alert" style="height:1.2em;">
  {% if mensagem %}
    {{ mensagem }}
  {% endif %}
</div>

<div id="login-container" style="display:none; max-width:320px; margin:0 auto; text-align:center;">
  <h2>Área Privada</h2>
  <form id="form-login" method="POST" onsubmit="return false;">
    <input type="password" id="senha" name="senha" placeholder="Digite a senha" required autocomplete="off"/>
    <br/>
    <button id="btn-login" type="submit">Entrar</button>
    <button id="btn-voltar" type="button">Voltar</button>
    <div id="erro-senha" class="alert error" style="height:1.2em; margin-top:8px;"></div>
  </form>
</div>

<div id="form-coords">
  <input type="number" id="latitude" step="any" placeholder="Latitude"/>
  <input type="number" id="longitude" step="any" placeholder="Longitude"/>
  <button id="btn-mostrar" disabled>Mostrar no Mapa</button>
</div>
<div id="map"></div>
</main>
<footer>Este sistema é fictício e destina-se exclusivamente a fins académicos e demonstrativos. Nenhuma informação aqui representa dados reais.</footer>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
const map = L.map('map').setView([41.1578, -8.6291], 12);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);

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

function carregarCasas(){
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
}

carregarCasas();

function validarCampos(){
  const lat = document.getElementById('latitude');
  const lng = document.getElementById('longitude');
  let valido = true;

  // Limpar erros visuais
  lat.classList.remove('error');
  lng.classList.remove('error');

  if(lat.value.trim() === '') {
    lat.classList.add('error');
    valido = false;
  }
  if(lng.value.trim() === '') {
    lng.classList.add('error');
    valido = false;
  }

  document.getElementById('btn-mostrar').disabled = !valido;
  return valido;
}

document.getElementById('latitude').addEventListener('input', validarCampos);
document.getElementById('longitude').addEventListener('input', validarCampos);

document.getElementById('btn-mostrar').addEventListener('click', function(){
  if(!validarCampos()) return; // Não permitir clique se inválido

  const lat = parseFloat(document.getElementById('latitude').value);
  const lng = parseFloat(document.getElementById('longitude').value);
  fetch(`/get_certificado?lat=${lat}&lng=${lng}`).then(r=>r.json()).then(c=>{
    if(!c.latitude){
      alert('Casa não encontrada');
      return;
    }
    const cor = cores[c.certificado]||cores[''];
    const icon = criarIcone(cor);
    const mark = L.marker([c.latitude,c.longitude],{icon}).addTo(map);
    let texto = `<strong>${c.morada}</strong><br>
                 ${c.descricao}<br>
                 Latitude: ${c.latitude.toFixed(5)}<br>
                 Longitude: ${c.longitude.toFixed(5)}<br>
                 Certificado: <strong>${c.certificado}</strong>`;
    if(c.proprietario) texto += `<br><em>Proprietário: ${c.proprietario}</em>`;
    mark.bindPopup(texto).openPopup();
    map.setView([c.latitude,c.longitude],16);
  }).catch(_=>alert('Erro ao buscar casa'));
});

// -------------------- Login --------------------

const loginContainer = document.getElementById('login-container');
const abrirLogin = document.getElementById('abrir-login');
const btnVoltar = document.getElementById('btn-voltar');
const formLogin = document.getElementById('form-login');
const senhaInput = document.getElementById('senha');
const btnLogin = document.getElementById('btn-login');
const erroSenha = document.getElementById('erro-senha');
const mensagemDiv = document.getElementById('mensagem');

if(abrirLogin){
  abrirLogin.addEventListener('click', () => {
    loginContainer.style.display = 'block';
    abrirLogin.style.display = 'none';
    erroSenha.textContent = '';
    senhaInput.value = '';
    senhaInput.focus();
  });
}

btnVoltar.addEventListener('click', () => {
  loginContainer.style.display = 'none';
  abrirLogin.style.display = 'inline';
  erroSenha.textContent = '';
  senhaInput.value = '';
});

formLogin.addEventListener('submit', async (e) => {
  e.preventDefault();
  erroSenha.textContent = '';
  btnLogin.disabled = true;

  const senha = senhaInput.value.trim();
  if (!senha) {
    erroSenha.textContent = 'Por favor, digite a senha.';
    btnLogin.disabled = false;
    return;
  }

  // Enviar via fetch para login
  try {
    const response = await fetch('/login', {
      method: 'POST',
      headers: {'Content-Type': 'application/x-www-form-urlencoded'},
      body: new URLSearchParams({senha})
    });
    const text = await response.text();
    if (text.includes('Senha incorreta')) {
      erroSenha.textContent = 'Senha incorreta!';
      btnLogin.disabled = false;
      senhaInput.focus();
    } else {
      // Login OK - recarregar página para atualizar estado
      location.reload();
    }
  } catch (err) {
    erroSenha.textContent = 'Erro na conexão.';
    btnLogin.disabled = false;
  }
});

// -------------------- Logout --------------------

function confirmarLogout(){
  if(confirm('Deseja realmente sair?')){
    fetch('/logout').then(() => {
      mensagemDiv.textContent = 'Logout realizado com sucesso.';
      mensagemDiv.classList.remove('error');
      loginContainer.style.display = 'none';
      if(abrirLogin) abrirLogin.style.display = 'inline';
      // Ocultar a mensagem após 2s
      setTimeout(() => { mensagemDiv.textContent = ''; }, 2000);
      location.reload();
    });
  }
}

// Mostrar mensagem de sucesso login/logout por 2 segundos
window.onload = () => {
  if (mensagemDiv.textContent.trim() !== '') {
    setTimeout(() => {
      mensagemDiv.style.opacity = '0';
      setTimeout(() => {
        mensagemDiv.textContent = '';
        mensagemDiv.style.opacity = '1';
      }, 500);
    }, 2000);
  }
};
</script>
</body>
</html>"""

@app.route('/')
def index():
    mensagem = session.pop('mensagem', '')
    return render_template_string(HTML, session=session, mensagem=mensagem)

@app.route('/login', methods=['POST'])
def login():
    senha = request.form.get('senha', '')
    if senha == 'Adming3':
        session['logado'] = True
        session['mensagem'] = 'Login efetuado com sucesso!'
        return 'Login efetuado com sucesso!'
    else:
        return 'Senha incorreta'

@app.route('/logout')
def logout():
    session.pop('logado', None)
    session['mensagem'] = 'Logout realizado com sucesso.'
    return ('', 204)

@app.route('/todas_casas')
def todas_casas():
    if folha_casa is None:
        return jsonify([])
    dados = folha_casa.get_all_records()
    casas = []
    for d in dados:
        try:
            casa = {
                'descricao': d.get('Descrição', ''),
                'morada': d.get('Morada', ''),
                'latitude': float(d.get('Latitude', 0)),
                'longitude': float(d.get('Longitude', 0)),
                'certificado': d.get('Certificado energético', '').strip().upper(),
                'proprietario': d.get('Proprietário', '') if session.get('logado') else ''
            }
            casas.append(casa)
        except Exception:
            continue
    return jsonify(casas)

@app.route('/get_certificado')
def get_certificado():
    if folha_casa is None:
        return jsonify({})
    lat = request.args.get('lat', type=float)
    lng = request.args.get('lng', type=float)
    dados = folha_casa.get_all_records()
    for d in dados:
        try:
            if abs(float(d.get('Latitude', 0)) - lat) < 0.0001 and abs(float(d.get('Longitude', 0)) - lng) < 0.0001:
                return jsonify({
                    'descricao': d.get('Descrição', ''),
                    'morada': d.get('Morada', ''),
                    'latitude': float(d.get('Latitude', 0)),
                    'longitude': float(d.get('Longitude', 0)),
                    'certificado': d.get('Certificado energético', '').strip().upper(),
                    'proprietario': d.get('Proprietário', '') if session.get('logado') else ''
                })
        except Exception:
            continue
    return jsonify({})

if __name__ == '__main__':
    app.run(debug=True)
