from flask import Flask, render_template_string, request, session, redirect, url_for
import gspread
from google.oauth2.service_account import Credentials
import json

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta'

# Autenticação com Google Sheets
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = Credentials.from_service_account_file('credenciais.json', scopes=scope)
client = gspread.authorize(creds)

sheet_casas = client.open("Dados Casa").worksheet("Casas")
sheet_consumos = client.open("Dados Consumos").worksheet("Consumos")

def get_casas():
    dados = sheet_casas.get_all_records()
    return dados

def get_consumos_por_id(id_casa):
    todos = sheet_consumos.get_all_records()
    return [c for c in todos if str(c["ID Casa"]) == str(id_casa)]

@app.route('/')
def index():
    casas = get_casas()
    casas_json = json.dumps(casas)
    logged_in = 'user' in session
    nome_proprietario = session['user']['Proprietário'] if logged_in else None
    consumos = get_consumos_por_id(session['user']['ID']) if logged_in else []

    return render_template_string('''
<!DOCTYPE html>
<html lang="pt">
<head>
    <meta charset="UTF-8">
    <title>Gestão de Consumo</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css" />
    <style>
        body {
            margin: 0;
            font-family: 'Segoe UI', sans-serif;
            background-color: #111;
            color: #eee;
        }
        header {
            background: linear-gradient(90deg, #0f0f0f, #1a1a1a);
            padding: 1rem;
            text-align: center;
            color: #0ff;
            font-size: 2rem;
            font-weight: bold;
            box-shadow: 0 2px 10px #000;
        }
        header a {
            text-decoration: none;
            color: #0ff;
        }
        #map {
            height: 60vh;
            width: 100%;
        }
        .container {
            padding: 2rem;
        }
        .login-form, .consumos {
            background-color: #1e1e1e;
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: 0 0 15px rgba(0, 255, 255, 0.2);
            margin-top: 2rem;
        }
        .consumos h2 {
            color: #0ff;
            text-shadow: 0 0 5px #0ff;
            font-size: 1.8rem;
        }
        table {
            width: 100%;
            margin-top: 1rem;
            border-collapse: collapse;
        }
        th, td {
            border: 1px solid #333;
            padding: 0.6rem;
            text-align: center;
        }
        th {
            background-color: #0ff;
            color: #000;
        }
        td {
            background-color: #222;
        }
        .btn {
            padding: 0.6rem 1.2rem;
            border: none;
            border-radius: 8px;
            background-color: #0ff;
            color: #000;
            cursor: pointer;
            font-weight: bold;
            transition: 0.3s;
        }
        .btn:hover {
            background-color: #00cccc;
        }
        .logout-link {
            color: #ff6666;
            font-weight: bold;
        }
        .warning {
            color: #f88;
            margin-top: 0.5rem;
        }
    </style>
</head>
<body>
    <header><a href="{{ url_for('index') }}">Gestão de Consumo</a></header>
    <div id="map"></div>
    <div class="container">
        {% if not logged_in %}
            <div class="login-form">
                <h2>Acesso à Área Privada</h2>
                <form method="post" action="{{ url_for('login') }}">
                    <label>ID da Casa:</label><br>
                    <input type="text" name="id"><br><br>
                    <label>Senha:</label><br>
                    <input type="password" name="senha"><br><br>
                    <button type="submit" class="btn">Entrar</button>
                </form>
                {% if session.get('erro') %}
                    <div class="warning">ID ou senha incorretos.</div>
                    {% set _ = session.pop('erro') %}
                {% endif %}
            </div>
        {% else %}
            <div class="consumos">
                <h2>Área Privada – Bem-vindo, {{ nome_proprietario }}</h2>
                <table>
                    <tr>
                        <th>Tipo</th>
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
                <br>
                <a href="{{ url_for('logout') }}" class="logout-link">Logout</a>
            </div>
        {% endif %}
    </div>

    <script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>
    <script>
        const casas = {{ casas_json|safe }};

        const map = L.map('map').setView([38.7169, -9.1399], 11);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; OpenStreetMap'
        }).addTo(map);

        casas.forEach(casa => {
            const cor = {
                'A': 'green',
                'B': 'lime',
                'C': 'yellow',
                'D': 'orange',
                'E': 'red',
                'F': 'darkred',
                'G': 'black'
            }[casa["Certificado Energético"].toUpperCase()] || 'gray';

            const marker = L.circleMarker([casa["Latitude"], casa["Longitude"]], {
                radius: 8,
                fillColor: cor,
                color: '#000',
                weight: 1,
                opacity: 1,
                fillOpacity: 0.9
            }).addTo(map);

            marker.bindPopup(
                `<b>${casa["Descrição"]}</b><br>` +
                `${casa["Morada"]}<br>` +
                `Certificado: <b>${casa["Certificado Energético"]}</b>`
            );
        });
    </script>
</body>
</html>
    ''', casas_json=casas_json, logged_in=logged_in, nome_proprietario=nome_proprietario, consumos=consumos)

@app.route('/login', methods=['POST'])
def login():
    id_input = request.form['id']
    senha_input = request.form['senha']
    casas = get_casas()
    for casa in casas:
        if str(casa['ID']) == id_input and str(casa['Senha']) == senha_input:
            session['user'] = casa
            return redirect(url_for('index'))
    session['erro'] = True
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    return '''
        <script>
            alert("Logout efetuado com sucesso.");
            window.location.href = "/";
        </script>
    '''

if __name__ == '__main__':
    app.run(debug=True)
