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
    print("Erro ao conectar Google Sheets:", e)
    folha_casa = None

HTML = """
<!DOCTYPE html>
<html lang="pt">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Gestão de Consumo</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<style>
html, body {
  margin:0; padding:0; height:100%;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  background-color: #f4f7f9;
  color: #333;
  overflow-x: hidden;
}
header {
  background-color: #0077cc;
  color: white;
  padding: 1rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
}
header h1 {
  margin: 0;
  font-weight: 600;
  font-size: 1.8rem;
}
header h1 a {
  color: white;
  text-decoration: none;
}
#header-right {
  display: flex;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;
}
#header-right a, #header-right span {
  font-size: 1rem;
  color: white;
  text-decoration: none;
  cursor: pointer;
}
#header-right a:hover, #header-right span:hover {
  text-decoration: underline;
}
main {
  padding: 20px;
  max-width: 960px;
  margin: 0 auto;
}
#form-coords {
  text-align: center;
  display: flex;
  justify-content: center;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 10px;
}
input[type="number"], input[type="text"], input[type="password"] {
  padding: 10px;
  margin: 8px 0;
  width: 200px;
  max-width: 90%;
  border-radius: 6px;
  border: 1px solid #ccc;
  box-sizing: border-box;
  transition: border-color 0.3s ease;
  font-size: 1rem;
}
input.error {
  border-color: red !important;
  outline: none;
}
button {
  padding: 10px 16px;
  border: none;
  border-radius: 6px;
  background-color: #0077cc;
  color: white;
  cursor: pointer;
  font-size: 1rem;
  min-width: 120px;
  transition: background-color 0.3s ease;
}
button:disabled {
  background-color: #a0c4e3;
  cursor: not-allowed;
}
button:hover:not(:disabled) {
  background-color: #005fa3;
}
#map {
  height: 500px;
  width: 100%;
  border-radius: 10px;
  box-shadow: 0 0 12px rgba(0,0,0,0.15);
  background-color: lightgray;
  margin-top: 10px;
}
footer {
  background-color: #222;
  color: #ccc;
  text-align: center;
  padding: 15px 20px;
  font-size: 0.9em;
  width: 100%;
  margin-top: 40px;
}
/* Mensagens de alerta */
.alert {
  color: green;
  font-weight: bold;
  text-align: center;
  margin-top: 5px;
  opacity: 1;
  transition: opacity 0.5s ease;
  user-select: none;
  min-height: 1.2em;
}
.alert.error {
  color: red;
}

/* Modal login */
#login-modal {
  display: none;
  position: fixed;
  top: 0; left: 0; right:0; bottom:0;
  background-color: rgba(0,0,0,0.5);
  z-index: 9999;
  justify-content: center;
  align-items: center;
}
#login-modal.active {
  display: flex;
}
#login-box {
  background-color: white;
  padding: 30px 25px;
  border-radius: 10px;
  width: 320px;
  max-width: 90%;
  box-shadow: 0 5px 20px rgba(0,0,0,0.3);
  text-align: center;
}
#login-box h2 {
  margin-top: 0;
  margin-bottom: 15px;
}
#login-box form {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
#login-box input[type="password"] {
  width: 100%;
  font-size: 1rem;
  padding: 10px;
  border-radius: 6px;
  border: 1px solid #ccc;
  transition: border-color 0.3s ease;
}
#login-box input.error {
  border-color: red !important;
  outline: none;
}
#login-box button {
  padding: 10px;
  border-radius: 6px;
  border: none;
  font-weight: 600;
}
#login-box button.login-btn {
  background-color: #0077cc;
  color: white;
  cursor: pointer;
  transition: background-color 0.3s ease;
}
#login-box button.login-btn:hover {
  background-color: #005fa3;
}
#login-box button.cancel-btn {
  background-color: #ccc;
  color: #333;
  cursor: pointer;
}
#login-box button.cancel-btn:hover {
  background-color: #bbb;
}

/* Responsividade */
@media (max-width:600px) {
  header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
    padding: 1rem;
  }
  #header-right {
    width: 100%;
    justify-content: space-between;
  }
  h1 {
    font-size: 1.5em;
  }
  #form-coords {
    flex-direction: column;
    align-items: center;
  }
  input, button {
    width: 90%;
    margin: 6px 0;
    min-width: unset;
  }
  #map {
    height: 300px;
  }
}
</style>
</head>
<body>

<header>
  <h1><a href="/">Gestão de Consumo</a></h1>
  <div id="header-right">
    <a href="https://github.com/WilkerJoseLopes/GestaoDeConsumo" target="_blank" rel="noopener">Sobre o projeto</a>
    {% if not session.get('logado') %}
      <span id="abrir-login" style="color:#eee; text-decoration:underline; cursor:pointer;">Área Privada</span>
    {% else %}
      <span id="logout-btn" style="cursor:pointer;">Logout</span>
    {% endif %}
  </div>
</header>

<main>
  <div id="mensagem" class="alert" style="height:1.2em;">
    {% if mensagem %}
      {{ mensagem }}
    {% endif %}
  </div>

  <div id="form-coords">
    <input type="number" id="latitude" step="any" placeholder="Latitude"/>
    <input type="number" id="longitude" step="any" placeholder="Longitude"/>
    <button id="btn-mostrar" disabled>Mostrar no Mapa</button>
  </div>
  <div id="map"></div>
</main>

<footer>
  Este sistema é fictício e destina-se exclusivamente a fins académicos e demonstrativos. Nenhuma informação aqui representa dados reais.
</footer>

<!-- Modal Login -->
<div id="login-modal" aria-hidden="true">
  <div id="login-box" role="dialog" aria-modal="true" aria-labelledby="login-title">
    <h2 id="login-title">Área Privada</h2>
    <form id="form-login" onsubmit="return false;">
      <input type="password" id="senha" name="senha" placeholder="Digite a senha" autocomplete="off" required aria-describedby="erro-senha"/>
      <div id="erro-senha" class="alert error" style="height:1.2em; margin-top:8px;"></div>
      <button class="login-btn" id="btn-login" type="submit">Entrar</button>
      <button class="cancel-btn" id="btn-cancel" type="button">Voltar</button>
    </form>
  </div>
</div>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
const mapa = L.map('map').setView([39.5, -8], 7);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{
  maxZoom: 18,
  attribution: '© OpenStreetMap'
}).addTo(mapa);

const certificadoCores = {
  'A+': '#1a9850',
  'A': '#66bd63',
  'B': '#d9ef8b',
  'C': '#fee08b',
  'D': '#fdae61',
  'E': '#f46d43',
  'F': '#d73027',
  'G': '#a50026'
};

let markers = [];

function limpaMarkers(){
  markers.forEach(m => mapa.removeLayer(m));
  markers = [];
}

function addCasasAoMapa(casas){
  limpaMarkers();
  casas.forEach(casa => {
    let cor = certificadoCores[casa.certificado] || '#666';
    let marker = L.circleMarker([casa.latitude, casa.longitude], {
      radius: 9,
      fillColor: cor,
      color: '#222',
      weight: 1,
      opacity: 1,
      fillOpacity: 0.8
    }).addTo(mapa);
    let popupConteudo = `<b>${casa.descricao}</b><br/>${casa.morada}<br/><b>Certificado:</b> ${casa.certificado || 'N/A'}`;
    if (casa.proprietario) popupConteudo += `<br/><i>Proprietário: ${casa.proprietario}</i>`;
    marker.bindPopup(popupConteudo);
    markers.push(marker);
  });
}

async function carregarCasas(){
  try {
    let resp = await fetch('/todas_casas');
    let dados = await resp.json();
    addCasasAoMapa(dados);
  } catch(e) {
    console.error("Erro ao carregar casas:", e);
  }
}
carregarCasas();

const latInput = document.getElementById('latitude');
const lngInput = document.getElementById('longitude');
const btnMostrar = document.getElementById('btn-mostrar');

function validaInputs(){
  let latVal = latInput.value.trim();
  let lngVal = lngInput.value.trim();
  let valido = true;

  if (!latVal){
    latInput.classList.add('error');
    valido = false;
  } else latInput.classList.remove('error');

  if (!lngVal){
    lngInput.classList.add('error');
    valido = false;
  } else lngInput.classList.remove('error');

  btnMostrar.disabled = !valido;
  return valido;
}

latInput.addEventListener('input', validaInputs);
lngInput.addEventListener('input', validaInputs);

btnMostrar.addEventListener('click', () => {
  if (!validaInputs()) return;
  let lat = parseFloat(latInput.value);
  let lng = parseFloat(lngInput.value);
  mapa.setView([lat, lng], 17);
});

// Mensagens temporizadas
function mostrarMensagem(texto, tipo = 'success'){
  const msgEl = document.getElementById('mensagem');
  msgEl.textContent = texto;
  msgEl.className = 'alert ' + (tipo === 'error' ? 'error' : '');
  setTimeout(() => {
    msgEl.textContent = '';
    msgEl.className = 'alert';
  }, 2000);
}

// LOGIN modal
const loginModal = document.getElementById('login-modal');
const abrirLoginBtn = document.getElementById('abrir-login');
const cancelarLoginBtn = document.getElementById('btn-cancel');
const btnLogin = document.getElementById('btn-login');
const senhaInput = document.getElementById('senha');
const erroSenha = document.getElementById('erro-senha');

abrirLoginBtn?.addEventListener('click', () => {
  loginModal.classList.add('active');
  senhaInput.value = '';
  erroSenha.textContent = '';
  senhaInput.classList.remove('error');
  senhaInput.focus();
});

cancelarLoginBtn.addEventListener('click', () => {
  loginModal.classList.remove('active');
});

btnLogin.addEventListener('click', async () => {
  const senha = senhaInput.value.trim();
  if (!senha) {
    erroSenha.textContent = 'Digite a senha.';
    senhaInput.classList.add('error');
    return;
  }
  try {
    const resp = await fetch('/login', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({senha})
    });
    const data = await resp.json();
    if (data.success){
      mostrarMensagem('Login efetuado com sucesso!');
      loginModal.classList.remove('active');
      erroSenha.textContent = '';
      senhaInput.classList.remove('error');
      // Atualiza página para mostrar logout e nome do proprietário
      setTimeout(() => location.reload(), 500);
    } else {
      erroSenha.textContent = 'Senha incorreta!';
      senhaInput.classList.add('error');
    }
  } catch {
    erroSenha.textContent = 'Erro no servidor.';
  }
});

// Logout com confirmação
const logoutBtn = document.getElementById('logout-btn');
logoutBtn?.addEventListener('click', () => {
  if (confirm('Tem certeza que deseja fazer logout?')) {
    fetch('/logout', {method: 'POST'}).then(() => {
      mostrarMensagem('Logout realizado com sucesso.');
      setTimeout(() => location.reload(), 2100);
    });
  }
});

</script>
</body>
</html>
"""

@app.route('/')
def index():
    mensagem = session.pop('mensagem', None)
    return render_template_string(HTML, mensagem=mensagem, session=session)

@app.route('/login', methods=['POST'])
def login():
    dados = request.json
    senha = dados.get('senha', '')
    if senha == '12345':  # senha hardcoded para exemplo
        session['logado'] = True
        session['proprietario'] = 'Proprietário Exemplo'
        return jsonify({"success": True})
    else:
        return jsonify({"success": False})

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('logado', None)
    session.pop('proprietario', None)
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

if __name__ == '__main__':
    app.run(debug=True)
