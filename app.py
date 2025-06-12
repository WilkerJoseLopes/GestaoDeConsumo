from flask import Flask, render_template_string, request, redirect, session
import gspread
from google.oauth2.service_account import Credentials

app = Flask(__name__)
app.secret_key = 'segredo_super_secreto'

# Conectar à API do Google Sheets
escopos = ["https://www.googleapis.com/auth/spreadsheets"]
credenciais = Credentials.from_service_account_file("credenciais.json", scopes=escopos)
cliente = gspread.authorize(credenciais)
planilha = cliente.open_by_url("https://docs.google.com/spreadsheets/d/1SKveqiaBaYqyQ5JadM59JKQhd__jodFZfjl78KUGa9w/edit")

# Abrir folhas
try:
    folha_casas = planilha.worksheet("Dados Casa")
except:
    folha_casas = None

try:
    folha_consumo = planilha.worksheet("Dados Consumo")
except:
    folha_consumo = None

# Página inicial
@app.route('/')
def index():
    casas = folha_casas.get_all_records() if folha_casas else []
    mensagem = session.pop("mensagem", None)

    # Criar HTML com Leaflet para mostrar casas no mapa
    html = """
    <!DOCTYPE html>
    <html lang="pt">
    <head>
      <meta charset="UTF-8">
      <title>Gestão de Consumo</title>
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
      <style>
        body { font-family: Arial, sans-serif; background: #f4f7f9; text-align: center; margin: 0; padding: 0; }
        h1 { background: #0077cc; color: white; margin: 0; padding: 20px; cursor: pointer; }
        #map { height: 500px; margin: 20px auto; width: 90%; max-width: 1000px; }
        .top { margin: 20px; }
        .msg { color: red; font-weight: bold; }
        form { margin: 20px; }
        input[type="password"] { padding: 5px; }
        input[type="submit"] { padding: 5px 10px; background: #0077cc; color: white; border: none; cursor: pointer; }
        .btn-sair { margin-top: 20px; display: inline-block; color: #0077cc; text-decoration: none; }
        .aviso { font-size: 0.9em; color: #555; margin-top: 30px; }
      </style>
    </head>
    <body>
      <h1 onclick="window.location.href='/'">Gestão de Consumo</h1>
      {% if not logado %}
      <div class="top">
        <form method="POST" action="/login">
          <label>Área Privada: <input type="password" name="senha" placeholder="Digite a senha"></label>
          <input type="submit" value="Entrar">
        </form>
      </div>
      {% else %}
      <p><a class="btn-sair" href="/logout" onclick="return confirm('Deseja sair?')">Sair da Área Privada</a></p>
      <p><a class="btn-sair" href="/area_privada">Ir para Área Privada</a></p>
      {% endif %}
      {% if mensagem %}<p class="msg">{{ mensagem }}</p>{% endif %}
      <div id="map"></div>
      <p class="aviso">Uso Acadêmico - Projeto de Demonstração</p>
      <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
      <script>
        var casas = {{ casas | tojson }};
        var mapa = L.map('map').setView([38.7, -9.1], 8);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
          attribution: '&copy; OpenStreetMap contributors'
        }).addTo(mapa);

        casas.forEach(function(casa) {
          var cor;
          switch(casa["Certificado Energético"].toUpperCase()) {
            case 'A': cor = 'green'; break;
            case 'B': cor = 'lime'; break;
            case 'C': cor = 'orange'; break;
            case 'D': cor = 'orangered'; break;
            case 'E': cor = 'red'; break;
            default: cor = 'gray';
          }
          var marcador = L.circleMarker([casa["Latitude"], casa["Longitude"]], {
            radius: 8,
            fillColor: cor,
            color: '#000',
            weight: 1,
            opacity: 1,
            fillOpacity: 0.8
          }).addTo(mapa);

          marcador.bindPopup(
            `<b>${casa["Descrição"]}</b><br>${casa["Morada"]}<br>Certificado: ${casa["Certificado Energético"]}`
          );
        });
      </script>
    </body>
    </html>
    """
    return render_template_string(html, casas=casas, mensagem=mensagem, logado=session.get('logado'))

# Login
@app.route('/login', methods=['POST'])
def login():
    senha = request.form.get('senha')
    if senha == 'Adming3':
        session['logado'] = True
        return redirect('/')
    else:
        session['mensagem'] = "Senha incorreta."
        return redirect('/')

# Logout
@app.route('/logout')
def logout():
    session.pop('logado', None)
    session['mensagem'] = "Logout realizado com sucesso."
    return redirect('/')

# Área Privada com tabela de consumo
@app.route('/area_privada')
def area_privada():
    if not session.get('logado'):
        session['mensagem'] = "Por favor, faça login para acessar a Área Privada."
        return redirect('/')

    if not folha_consumo:
        return "<h2>Erro ao carregar dados de consumo.</h2><p><a href='/'>Voltar</a></p>"

    registros = folha_consumo.get_all_records()
    tabela_html = """
    <h2>Consumos das Casas</h2>
    <table border="1" cellpadding="8" cellspacing="0" style="border-collapse:collapse; width:100%; max-width:900px; margin:auto;">
        <thead style="background:#0077cc; color:white;">
            <tr>
                <th>ID Casa</th>
                <th>Tipo Consumo</th>
                <th>Período</th>
                <th>Valor</th>
                <th>Unidade</th>
                <th>Custo (€)</th>
            </tr>
        </thead>
        <tbody>
    """

    for r in registros:
        tabela_html += f"""
        <tr>
            <td>{r.get('ID Casa','')}</td>
            <td>{r.get('Tipo Consumo','')}</td>
            <td>{r.get('Período','')}</td>
            <td>{r.get('Valor','')}</td>
            <td>{r.get('Unidade','')}</td>
            <td>{r.get('Custo (€)','')}</td>
        </tr>
        """

    tabela_html += "</tbody></table>"

    html = f"""
    <!DOCTYPE html>
    <html lang="pt">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1"/>
      <title>Área Privada - Consumos</title>
      <style>
        body {{
          font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
          background-color: #f4f7f9; color: #333;
          margin: 0; padding: 20px;
          display: flex; flex-direction: column; align-items: center;
          min-height: 100vh;
        }}
        h2 {{ color: #0077cc; margin-bottom: 20px; }}
        table {{ background: white; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); overflow: hidden; }}
        th, td {{ text-align: center; padding: 10px 15px; }}
        tbody tr:nth-child(odd) {{ background: #f9f9f9; }}
        a {{ margin-top: 20px; color: #0077cc; text-decoration: none; font-weight: 600; }}
        a:hover {{ text-decoration: underline; }}
      </style>
    </head>
    <body>
      {tabela_html}
      <a href="/">Voltar</a>
    </body>
    </html>
    """

    return html

if __name__ == '__main__':
    app.run(debug=True)
