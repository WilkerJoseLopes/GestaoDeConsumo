from flask import Flask, render_template_string, request, jsonify, session, redirect
import os, json, gspread
from google.oauth2.service_account import Credentials

app = Flask(__name__)
app.secret_key = 'segredo_super_secreto'

# Conexão com Google Sheets
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
try:
    GOOGLE_CREDENTIALS = json.loads(os.getenv("GOOGLE_CREDENTIALS"))
    creds = Credentials.from_service_account_info(GOOGLE_CREDENTIALS, scopes=SCOPES)
    client = gspread.authorize(creds)
    planilha = client.open_by_key("1SKveqiaBaYqyQ5JadM59JKQhd__jodFZfjl78KUGa9w")
    folha_casa = planilha.worksheet("Dados Casa")
    folha_consumos = planilha.worksheet("Dados Consumos")
except Exception as e:
    print("Erro ao conectar ao Google Sheets:", e)
    folha_casa = None
    folha_consumos = None

# Função para obter dados da aba Consumos
def obter_consumos_por_casa():
    if not folha_consumos:
        return []
    registros = folha_consumos.get_all_records()
    consumos = {}
    for reg in registros:
        casa_id = reg['ID Casa']
        if casa_id not in consumos:
            consumos[casa_id] = []
        consumos[casa_id].append(reg)
    return consumos

@app.route('/')
def index():
    consumos = obter_consumos_por_casa() if session.get('logado') else {}
    mensagem = session.pop('mensagem', '')
    return render_template_string(HTML, session=session, mensagem=mensagem, consumos=consumos)

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
    session['mensagem'] = 'Logout realizado com sucesso.'
    return redirect('/')

@app.route('/todas_casas')
def todas_casas():
    if not folha_casa:
        return jsonify([])
    regs = folha_casa.get_all_records()
    casas = []
    for reg in regs:
        try:
            casa = {
                'latitude': float(reg.get('Latitude', 0)),
                'longitude': float(reg.get('Longitude', 0)),
                'morada': reg.get('Morada', ''),
                'descricao': reg.get('Descrição', ''),
                'certificado': reg.get('Certificado Energético', '').strip()
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
    if not folha_casa or lat is None or lng is None:
        return jsonify({})
    for reg in folha_casa.get_all_records():
        try:
            if abs(float(reg.get('Latitude', 0)) - lat) < 1e-5 and abs(float(reg.get('Longitude', 0)) - lng) < 1e-5:
                casa = {
                    'latitude': float(reg.get('Latitude', 0)),
                    'longitude': float(reg.get('Longitude', 0)),
                    'morada': reg.get('Morada', ''),
                    'descricao': reg.get('Descrição', ''),
                    'certificado': reg.get('Certificado Energético', '').strip()
                }
                if session.get('logado'):
                    casa['proprietario'] = reg.get('Proprietário', '')
                return jsonify(casa)
        except:
            pass
    return jsonify({})

# HTML INLINE COM ÁREA DE CONSUMOS
HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Gestão de Consumo</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; margin: 0; background-color: #f0f0f0; color: #333; }
        header { background-color: #004080; color: white; padding: 10px; text-align: center; }
        main { padding: 20px; }
        .msg { color: green; font-weight: bold; }
        #map { height: 400px; margin-top: 20px; }
        button { margin: 5px; padding: 5px 10px; }
        .nasa-box {
            background: #000;
            color: #0ff;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 0 10px cyan;
            margin-top: 30px;
        }
        .nasa-box h2 {
            text-align: center;
            font-size: 2rem;
        }
        .nasa-box table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
            background-color: #111;
        }
        .nasa-box th, .nasa-box td {
            border: 1px solid #0ff;
            padding: 8px;
            text-align: center;
        }
        .nasa-box th {
            background-color: #222;
        }
    </style>
    <link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css" />
</head>
<body>
<header>
    <h1><a href="/" style="color:white; text-decoration:none;">Gestão de Consumo</a></h1>
    {% if session.get('logado') %}
        <p>Bem-vindo à Área Privada! <a href="/logout" onclick="return confirm('Deseja sair?')">Logout</a></p>
    {% else %}
        <button onclick="document.getElementById('login').style.display='block'">Área Privada</button>
    {% endif %}
</header>
<main>
    {% if mensagem %}
        <p class="msg">{{ mensagem }}</p>
    {% endif %}
    <div id="map"></div>

    <!-- Área Privada com Consumos -->
    {% if session.get('logado') %}
        <div class="nasa-box">
            <h2>🔬 Painel de Consumo Energético</h2>
            {% if not consumos %}
                <p style="text-align:center;">Nenhum dado disponível.</p>
            {% else %}
                {% for casa, registos in consumos.items() %}
                    <div style="margin-bottom:30px;">
                        <h3>🏠 Casa {{ casa }}</h3>
                        <table>
                            <tr>
                                <th>Tipo</th><th>Período</th><th>Valor</th><th>Unidade</th><th>Custo (€)</th>
                            </tr>
                            {% for item in registos %}
                                <tr>
                                    <td>{{ item['Tipo Consumo'] }}</td>
                                    <td>{{ item['Período'] }}</td>
                                    <td>{{ item['Valor'] }}</td>
                                    <td>{{ item['Unidade'] }}</td>
                                    <td>{{ item['Custo (€)'] }}</td>
                                </tr>
                            {% endfor %}
                        </table>
                    </div>
                {% endfor %}
            {% endif %}
        </div>
    {% endif %}

    <!-- Modal de Login -->
    <div id="login" style="display:none;">
        <p>Digite a senha:</p>
        <input type="password" id="senha" />
        <button onclick="verificaSenha()">Entrar</button>
        <button onclick="document.getElementById('login').style.display='none'">Cancelar</button>
    </div>
</main>
<script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>
<script>
    const map = L.map('map').setView([39.5, -8], 7);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19 }).addTo(map);

    fetch("/todas_casas")
        .then(res => res.json())
        .then(casas => {
            casas.forEach(casa => {
                const cor = getCorPorCertificado(casa.certificado);
                const marker = L.circleMarker([casa.latitude, casa.longitude], {
                    radius: 8, color: cor, fillColor: cor, fillOpacity: 0.8
                }).addTo(map);
                let info = `<b>${casa.descricao}</b><br>${casa.morada}<br>Certificado: ${casa.certificado}`;
                if (casa.proprietario) info += `<br>Proprietário: ${casa.proprietario}`;
                marker.bindPopup(info);
            });
        });

    function getCorPorCertificado(cert) {
        const cores = {
            'A+': 'green', 'A': '#66cc00', 'B': '#cddc39', 'C': '#ffc107',
            'D': '#ff9800', 'E': '#ff5722', 'F': '#f44336', 'G': 'red'
        };
        return cores[cert] || 'gray';
    }

    function verificaSenha() {
        const senha = document.getElementById('senha').value;
        fetch('/verifica_senha', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ senha })
        }).then(res => res.json()).then(data => {
            if (data.ok) location.reload();
            else alert("Senha incorreta.");
        });
    }
</script>
</body>
</html>
"""

if __name__ == '__main__':
    app.run(debug=True)
