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
<html lang=\"pt\">
<head>
  <meta charset=\"UTF-8\"/>
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\"/>
  <title>Gestão de Consumo</title>
  <link rel=\"stylesheet\" href=\"https://unpkg.com/leaflet@1.9.4/dist/leaflet.css\"/>
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
    input[type=\"number\"], input[type=\"text\"], input[type=\"password\"] {
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
    table {
      width:100%; border-collapse:collapse; margin-top:20px;
    }
    th, td {
      padding:10px; border:1px solid #ccc; text-align:left;
    }
    th {
      background-color:#0077cc; color:white;
    }
    .consumos-box {
      background:white; border-radius:10px; padding:20px;
      box-shadow:0 0 10px rgba(0,0,0,0.1);
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
  <h1><a href=\"/\">Gestão de Consumo</a></h1>
  <div id=\"header-right\">
    <a href=\"https://github.com/WilkerJoseLopes/GestaoDeConsumo\" target=\"_blank\">Sobre o projeto</a>
    {% if not session.get('logado') %}
      <span onclick=\"abrirLogin()\">Área Privada</span>
    {% else %}
      <span onclick=\"confirmarLogout()\">Logout</span>
    {% endif %}
  </div>
</header>

<main>
  {% if mensagem %}
    <div class=\"alert\">{{ mensagem }}</div>
  {% endif %}
  <div id=\"form-coords\">
    <input type=\"number\" id=\"latitude\" step=\"any\" placeholder=\"Latitude\"/>
    <input type=\"number\" id=\"longitude\" step=\"any\" placeholder=\"Longitude\"/>
    <button onclick=\"adicionarMarcador()\">Mostrar no Mapa</button>
  </div>
  <div id=\"map\"></div>

  {% if session.get('logado') and consumos %}
    <div class=\"consumos-box\">
      <h2>Consumos do Proprietário</h2>
      <table>
        <tr>
          <th>Casa</th><th>Tipo</th><th>Período</th><th>Valor</th><th>Unidade</th><th>Custo (€)</th>
        </tr>
        {% for c in consumos %}
        <tr>
          <td>{{ c.id_casa }}</td>
          <td>{{ c.tipo }}</td>
          <td>{{ c.periodo }}</td>
          <td>{{ c.valor }}</td>
          <td>{{ c.unidade }}</td>
          <td>{{ c.custo }}</td>
        </tr>
        {% endfor %}
      </table>
    </div>
  {% endif %}
</main>

<div id=\"loginModal\">
  <div id=\"loginModalContent\">
    <h3>Área Privada</h3>
    <input type=\"password\" id=\"senhaInput\" placeholder=\"Digite a senha\" />
    <br/>
    <button onclick=\"enviarSenha()\">Entrar</button>
    <button onclick=\"fecharLogin()\">Cancelar</button>
    <p id=\"erroSenha\" style=\"color:red; font-weight:bold;\"></p>
  </div>
</div>

<footer>
  Este sistema é fictício e destina-se exclusivamente a fins académicos e demonstrativos.
</footer>

<script src=\"https://unpkg.com/leaflet@1.9.4/dist/leaflet.js\"></script>
<script>
// ... scripts idênticos anteriores ...
</script>
</body>
</html>
"""

def buscar_consumos_por_proprietario(nome):
    if not folha_consumo:
        return []
    try:
        dados = folha_consumo.get_all_records()
        return [
            {
                'id_casa': linha.get('ID Casa', ''),
                'tipo': linha.get('Tipo Consumo', ''),
                'periodo': linha.get('Período', ''),
                'valor': linha.get('Valor', ''),
                'unidade': linha.get('Unidade', ''),
                'custo': linha.get('Custo (€)', '')
            }
            for linha in dados if linha.get('Proprietário', '').strip().lower() == nome.strip().lower()
        ]
    except Exception as e:
        print("Erro ao buscar consumos:", e)
        return []

@app.route('/')
def index():
    consumos = []
    if session.get('logado') and session.get('proprietario'):
        consumos = buscar_consumos_por_proprietario(session['proprietario'])
    return render_template_string(HTML, session=session, mensagem=session.pop('mensagem', ''), consumos=consumos)

@app.route('/verifica_senha', methods=['POST'])
def verifica_senha():
    senha = request.json.get('senha')
    if senha == 'Adming3':
        session['logado'] = True
        session['proprietario'] = 'Carlos Silva'  # ou extrair dinamicamente
        return jsonify(ok=True)
    return jsonify(ok=False)

@app.route('/logout')
def logout():
    session.clear()
    session['mensagem'] = 'Logout realizado com sucesso.'
    return redirect('/')

@app.route('/todas_casas')
def todas_casas():
    casas = []
    if folha_casa:
        try:
            dados = folha_casa.get_all_records()
            for d in dados:
                try:
                    lat = float(d.get('Latitude', 0))
                    lng = float(d.get('Longitude', 0))
                    casas.append({
                        'latitude': lat,
                        'longitude': lng,
                        'descricao': d.get('Descrição', ''),
                        'morada': d.get('Morada', ''),
                        'certificado': d.get('Certificado Energético', '').strip(),
                        'proprietario': d.get('Proprietário', '') if session.get('logado') else ''
                    })
                except Exception:
                    continue
        except Exception as e:
            print("Erro leitura dados casas:", e)
    return jsonify(casas)

@app.route('/get_certificado')
def get_certificado():
    lat = request.args.get('lat', type=float)
    lng = request.args.get('lng', type=float)
    if not (lat and lng and folha_casa):
        return jsonify({})
    try:
        dados = folha_casa.get_all_records()
        for d in dados:
            try:
                lat_c = float(d.get('Latitude', 0))
                lng_c = float(d.get('Longitude', 0))
                if abs(lat - lat_c) < 0.0001 and abs(lng - lng_c) < 0.0001:
                    return jsonify({
                        'latitude': lat_c,
                        'longitude': lng_c,
                        'descricao': d.get('Descrição', ''),
                        'morada': d.get('Morada', ''),
                        'certificado': d.get('Certificado energético', '').strip(),
                        'proprietario': d.get('Proprietário', '') if session.get('logado') else ''
                    })
            except Exception:
                continue
    except Exception as e:
        print("Erro leitura casa:", e)
    return jsonify({})

if __name__ == '__main__':
    app.run(debug=True)
