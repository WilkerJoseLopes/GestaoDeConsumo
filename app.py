import os
import json
import gspread
from flask import Flask, render_template_string, request, jsonify, session, redirect
from google.oauth2.service_account import Credentials
from collections import defaultdict

app = Flask(__name__)
app.secret_key = 'segredo_super_secreto'

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# --- Inicialização do Google Sheets ---
try:
    GOOGLE_CREDENTIALS = json.loads(os.getenv("GOOGLE_CREDENTIALS"))
    creds = Credentials.from_service_account_info(GOOGLE_CREDENTIALS, scopes=SCOPES)
    client = gspread.authorize(creds)
    planilha = client.open_by_key("1SKveqiaBaYqyQ5JadM59JKQhd__jodFZfjl78KUGa9w")
    folha_casa = planilha.worksheet("Dados Casa")
    folha_consumos = planilha.worksheet("Dados Consumos")
except Exception as e:
    print("Erro init Google Sheets:", e)
    folha_casa = folha_consumos = None
# --------------------------------------

HTML = """<!DOCTYPE html>
<html lang="pt">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>Gestão de Consumo</title>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
  <style>
    /* --- não altere nada nesta seção --- */
    html, body {margin:0; padding:0; height:100%}
    body {
      font-family:'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      display:flex; flex-direction:column; min-height:100vh;
      background-color:#f4f7f9; color:#333;
    }
    header { background-color:#0077cc; color:white; padding:1rem 2rem;
      display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; }
    header h1 a { color:white; text-decoration:none; }
    #header-right a, #header-right span { color:white; text-decoration:none; cursor:pointer; }
    #map { height:500px; width:100%; border-radius:10px;
      box-shadow:0 0 12px rgba(0,0,0,0.15); background-color:lightgray; }
    /* ------------------------------------ */

    /* Tabela de consumos (após login) */
    .tabela {
      margin:20px auto; max-width:960px;
      background:white; padding:20px; border-radius:8px;
      box-shadow:0 0 10px rgba(0,0,0,0.1);
    }
    .tabela table {
      width:100%; border-collapse:collapse;
    }
    .tabela th, .tabela td {
      border:1px solid #ddd; padding:8px; text-align:left;
    }
    .tabela th {
      background:#0077cc; color:white;
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

  <div id="map"></div>

  {% if session.get('logado') and consumos %}
  <div class="tabela">
    <h2>Consumos</h2>
    <table>
      <tr>
        <th>Tipo Consumo</th>
        <th>Período</th>
        <th>Valor</th>
        <th>Unidade</th>
        <th>Custo (€)</th>
      </tr>
      {% for c in consumos %}
      <tr>
        <td>{{ c['Tipo Consumo'] }}</td>
        <td>{{ c['Período'] }}</td>
        <td>{{ c['Valor'] }}</td>
        <td>{{ c['Unidade'] }}</td>
        <td>{{ c['Custo (€)'] }}</td>
      </tr>
      {% endfor %}
    </table>
    <div style="margin-top:10px;">
      <strong>Resumo de Custos:</strong>
      <ul>
        {% for tipo, val in resumo.items() %}
        <li>{{ tipo }}: €{{ "%.2f"|format(val) }}</li>
        {% endfor %}
        <li><strong>Total: €{{ "%.2f"|format(total) }}</strong></li>
      </ul>
    </div>
  </div>
  {% endif %}
</main>

<!-- Modal de Login (não mexer) -->
<div id="loginModal" style="display:none;position:fixed;top:0;left:0;
     width:100%;height:100%;background:rgba(0,0,0,0.5);justify-content:center;align-items:center;">
  <div style="background:white;padding:30px;border-radius:10px;text-align:center;">
    <h3>Área Privada</h3>
    <input type="password" id="senhaInput" placeholder="Digite a senha" />
    <br/><br/>
    <button onclick="enviarSenha()">Entrar</button>
    <button onclick="fecharLogin()">Cancelar</button>
    <p id="erroSenha" style="color:red;font-weight:bold;"></p>
  </div>
</div>

<footer>
  Este sistema é fictício e destina-se exclusivamente a fins académicos e demonstrativos.
</footer>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
// --- não mexer nesta parte ---
function confirmarLogout(){
  if(confirm("Deseja realmente sair?")){
    window.location.href="/logout";
  }
}
function abrirLogin(){
  document.getElementById("loginModal").style.display="flex";
}
function fecharLogin(){
  document.getElementById("loginModal").style.display="none";
  document.getElementById("erroSenha").textContent="";
  document.getElementById("senhaInput").value="";
}
function enviarSenha(){
  const s = document.getElementById("senhaInput").value;
  fetch("/verifica_senha",{method:"POST",
    headers:{"Content-Type":"application/json"},
    body:JSON.stringify({senha:s})
  }).then(r=>r.json()).then(res=>{
    if(res.ok) location.reload();
    else document.getElementById("erroSenha").textContent="Senha incorreta!";
  });
}

const map = L.map('map').setView([41.1578,-8.6291],12);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);

const cores = {
  'A+':'008000','A':'00AA00','A-':'33BB33','B+':'66CC00','B':'99CC00','B-':'BBD600',
  'C+':'CCCC00','C':'FFFF00','C-':'FFDD00','D+':'FFB300','D':'FFA500','D-':'FF8800',
  'E+':'FF6666','E':'FF0000','E-':'CC0000','F+':'A00000','F':'8B0000','F-':'660000',
  'G+':'444444','G':'000000','G-':'222222','':'0000FF'
};

function criarIcone(cor){
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" width="32" height="45" viewBox="0 0 32 45">
      <path fill="#${cor}" stroke="black" stroke-width="2"
            d="M16,1 C24.3,1 31,7.7 31,16 C31,27 16,44 16,44
               C16,44 1,27 1,16 C1,7.7 7.7,1 16,1 Z"/>
    </svg>`;
  return L.divIcon({html:svg,iconSize:[32,45],iconAnchor:[16,44],popupAnchor:[0,-40],className:''});
}

fetch('/todas_casas')
  .then(r=>r.json())
  .then(casas=>{
    casas.forEach(c=>{
      const icon = criarIcone(cores[c.certificado.trim()]||cores['']);
      const m = L.marker([c.latitude,c.longitude],{icon}).addTo(map);
      let texto = `<strong>${c.morada}</strong><br>${c.descricao}<br>
                   Certificado: <strong>${c.certificado}</strong>`;
      {% raw %}{% if session.get('logado') %}{% endraw %}
        texto += `<br><a href="/?casa={{casa_id_placeholder}}">Ver consumos</a>`;
      {% raw %}{% else %}{% endraw %}
        texto += `<br><em>Faça login para ver consumos</em>`;
      {% raw %}{% endif %}{% endraw %}
      m.bindPopup(texto);
    });
  });

</script>
</body>
</html>
"""

@app.route('/')
def index():
    # busca casas para o mapa
    return render_template_string(HTML, session=session, mensagem=session.pop('mensagem',''),
                                  consumos=[], resumo={}, total=0.0)

@app.route('/verifica_senha', methods=['POST'])
def verifica_senha():
    senha = request.json.get('senha')
    if senha == 'Adming3':
        session['logado']=True
        return jsonify(ok=True)
    return jsonify(ok=False)

@app.route('/logout')
def logout():
    session.clear()
    session['mensagem']='Logout realizado com sucesso.'
    return redirect('/')

@app.route('/todas_casas')
def todas_casas():
    casas=[]
    if not folha_casa: return jsonify(casas)
    for d in folha_casa.get_all_records():
        try:
            casas.append({
                'morada':d.get('Morada',''),
                'descricao':d.get('Descrição',''),
                'latitude':float(d.get('Latitude',0)),
                'longitude':float(d.get('Longitude',0)),
                'certificado':d.get('Certificado Energético','').strip()
            })
        except:
            continue
    return jsonify(casas)

@app.route('/', methods=['GET'])
def consumo_por_casa():
    # se não logado ou não clicou, não mostra tabela
    if not session.get('logado') or not request.args.get('casa'):
        return render_template_string(HTML, session=session, mensagem=session.pop('mensagem',''),
                                      consumos=[], resumo={}, total=0.0)

    # filtrar consumos da aba "Dados Consumos" só pelo registro clicado
    casa_idx = request.args.get('casa', type=int)
    registros = folha_consumos.get_all_records()
    consumos = []
    for r in registros:
        try:
            # supondo que a linha em Dados Consumos tenha um campo "Casa" com índice igual
            if int(r.get('Casa',-1)) == casa_idx:
                consumos.append(r)
        except:
            pass

    # montar resumo por tipo
    resumo=defaultdict(float)
    total=0.0
    for c in consumos:
        try:
            custo = float(c.get('Custo (€)',0))
            resumo[c.get('Tipo Consumo','Desconhecido')] += custo
            total += custo
        except:
            continue

    return render_template_string(HTML, session=session, mensagem='',
                                  consumos=consumos, resumo=resumo, total=total)

if __name__=='__main__':
    app.run(debug=True)
