import os
import json
import gspread
from flask import Flask, render_template_string, request, redirect, url_for, session, flash
from google.oauth2.service_account import Credentials

app = Flask(__name__)
app.secret_key = 'segredo'

# Acesso ao Google Sheets
creds = Credentials.from_service_account_file('credenciais.json', scopes=["https://www.googleapis.com/auth/spreadsheets"])
client = gspread.authorize(creds)
sheet = client.open("Casas_Consumo")

casas = sheet.worksheet("Casas").get_all_records()
consumos = sheet.worksheet("Dados Consumos").get_all_records()

HTML_BASE = """
<!DOCTYPE html>
<html lang="pt">
<head>
    <meta charset="UTF-8">
    <title>Gestão de Consumo</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        body {{
            font-family: 'Segoe UI', sans-serif;
            background: #0b0c10;
            color: #c5c6c7;
            margin: 0;
        }}
        header {{
            background: #1f2833;
            color: #66fcf1;
            padding: 1em;
            text-align: center;
        }}
        header h1 {{
            margin: 0;
            font-size: 2em;
        }}
        a {{
            color: #66fcf1;
            text-decoration: none;
        }}
        .content {{
            padding: 2em;
        }}
        #map {{
            height: 500px;
            border: 3px solid #45a29e;
            border-radius: 12px;
        }}
        .login-section, .private-section {{
            margin-top: 2em;
            background: #1f2833;
            padding: 2em;
            border-radius: 12px;
            box-shadow: 0 0 20px rgba(102, 252, 241, 0.4);
        }}
        input, button {{
            padding: 0.5em;
            font-size: 1em;
            border-radius: 8px;
            border: none;
            margin-top: 0.5em;
        }}
        .btn {{
            background-color: #66fcf1;
            color: #0b0c10;
            cursor: pointer;
        }}
        .btn:hover {{
            background-color: #45a29e;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 1em;
        }}
        th, td {{
            border: 1px solid #45a29e;
            padding: 0.75em;
            text-align: left;
        }}
        th {{
            background-color: #0b0c10;
            color: #66fcf1;
        }}
        .nasa-box {{
            background: linear-gradient(145deg, #0b0c10, #1f2833);
            box-shadow: 0 0 20px #66fcf1;
            padding: 2em;
            border-radius: 15px;
        }}
    </style>
</head>
<body>
    <header>
        <h1><a href="{{ url_for('index') }}">Gestão de Consumo</a></h1>
    </header>
    <div class="content">
        {content}
    </div>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        const casas = {casas_json};
        const mapa = L.map('map').setView([38.72, -9.14], 10);
        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png').addTo(mapa);

        casas.forEach(casa => {{
            let cor;
            switch (casa["Certificado Energético"]) {{
                case "A+": cor = "green"; break;
                case "A": cor = "lime"; break;
                case "B": cor = "yellow"; break;
                case "C": cor = "orange"; break;
                default: cor = "red";
            }}
            const marker = L.circleMarker([casa.Latitude, casa.Longitude], {{
                radius: 10,
                color: cor,
                fillOpacity: 0.8
            }}).addTo(mapa);
            marker.bindPopup(`<b>${{casa.Descrição}}</b><br>${{casa.Morada}}<br>Certificado: <b>${{casa["Certificado Energético"]}}</b>`);
        }});
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    casas_json = json.dumps(casas)
    content = '<div id="map"></div>'
    if 'logado' in session:
        user_casas = [c for c in casas if c['Código'] == session['codigo']]
        user_ids = [c['ID'] for c in user_casas]
        user_consumos = [c for c in consumos if c['ID Casa'] in user_ids]

        if user_consumos:
            content += '<div class="private-section nasa-box"><h2>Consumos da Sua Casa</h2>'
            content += '<table><tr><th>Tipo</th><th>Período</th><th>Valor</th><th>Unidade</th><th>Custo (€)</th></tr>'
            for consumo in user_consumos:
                content += f"<tr><td>{consumo['Tipo Consumo']}</td><td>{consumo['Período']}</td><td>{consumo['Valor']}</td><td>{consumo['Unidade']}</td><td>{consumo['Custo (€)']}</td></tr>"
            content += '</table>'
            content += '<p><a class="btn" href="/logout">Sair da Área Privada</a></p></div>'
        else:
            content += '<div class="private-section nasa-box"><p>Sem consumos registados.</p><a class="btn" href="/logout">Sair</a></div>'
    else:
        content += '''
        <div class="login-section">
            <h2>Área Privada</h2>
            <form method="POST" action="/login">
                <label for="codigo">Código do Proprietário:</label><br>
                <input type="password" name="codigo" id="codigo" required><br>
                <button class="btn" type="submit">Entrar</button>
            </form>
        </div>
        '''
    return render_template_string(HTML_BASE, content=content, casas_json=casas_json)

@app.route('/login', methods=['POST'])
def login():
    codigo = request.form['codigo']
    for casa in casas:
        if casa['Código'] == codigo:
            session['logado'] = True
            session['codigo'] = codigo
            flash("Login efetuado com sucesso!", "info")
            return redirect(url_for('index'))
    flash("Código inválido!", "error")
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    flash("Logout realizado com sucesso.", "info")
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
