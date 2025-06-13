import os
import json
from flask import Flask, render_template_string, request, redirect, session
import gspread
from google.oauth2.service_account import Credentials
from collections import defaultdict

app = Flask(__name__)
app.secret_key = "segredo"

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

# Autenticação com Google Sheets
GOOGLE_CREDENTIALS = json.loads(os.getenv("GOOGLE_CREDENTIALS"))
creds = Credentials.from_service_account_info(GOOGLE_CREDENTIALS, scopes=SCOPES)
client = gspread.authorize(creds)
casas_sheet = sheet.worksheet("Dados Casa")
consumos_sheet = sheet.worksheet("Dados Consumos")

@app.route("/", methods=["GET", "POST"])
def index():
    casas = casas_sheet.get_all_records()
    consumos_raw = consumos_sheet.get_all_records()
    consumos = []
    resumo = {}
    total = 0.0
    id_casa = session.get("id_casa")
    nome_proprietario = None

    if request.method == "POST":
        if "login" in request.form:
            id_casa = request.form.get("id_casa")
            senha = request.form.get("senha")
            for casa in casas:
                if str(casa["ID"]) == id_casa and casa["Código"] == senha:
                    session["logado"] = True
                    session["id_casa"] = id_casa
                    return redirect("/")
            return "<script>alert('Senha incorreta.');window.location='/'</script>"

        elif "logout" in request.form:
            session.clear()
            return "<script>alert('Logout efetuado com sucesso.');window.location='/'</script>"

        elif "cancelar_login" in request.form:
            return redirect("/")

    marcador_id = request.args.get("id")

    if marcador_id and session.get("logado"):
        session["id_casa"] = marcador_id
        id_casa = marcador_id

    if session.get("logado") and id_casa:
        # Filtrar consumos da casa
        for row in consumos_raw:
            if str(row["ID Casa"]) == str(id_casa):
                consumos.append(row)

        # Nome do proprietário
        for casa in casas:
            if str(casa["ID"]) == str(id_casa):
                nome_proprietario = casa.get("Proprietário", "Desconhecido")
                break

        # Filtro por período
        periodo = request.args.get("periodo")
        if periodo:
            consumos = [c for c in consumos if c["Período"] == periodo]

        # Calcular resumo
        resumo_temp = defaultdict(float)
        for c in consumos:
            try:
                custo = float(c["Custo (€)"])
                resumo_temp[c["Tipo Consumo"]] += custo
                total += custo
            except:
                pass
        resumo = dict(resumo_temp)

    return render_template_string("""
<!DOCTYPE html>
<html lang="pt">
<head>
    <meta charset="UTF-8">
    <title>Gestão de Consumo</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css"/>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 0; background: #111; color: white; }
        header { background: #222; padding: 10px 20px; display: flex; align-items: center; justify-content: space-between; }
        header h1 { color: #4fc3f7; cursor: pointer; margin: 0; }
        .map-container { height: 500px; }
        .form-box, .tabela { padding: 20px; }
        .form-box form, .tabela form { display: flex; flex-direction: column; gap: 10px; max-width: 300px; }
        input[type="text"], input[type="password"], select {
            padding: 8px; border-radius: 5px; border: none; outline: none;
        }
        input[type="submit"], button {
            padding: 10px; border: none; background: #4fc3f7; color: black;
            border-radius: 5px; cursor: pointer; font-weight: bold;
        }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { border: 1px solid #555; padding: 8px; text-align: left; }
        th { background: #333; }
        .resumo { margin-top: 20px; }
        footer { background: #222; padding: 10px 20px; font-size: 12px; text-align: center; color: #888; }
    </style>
</head>
<body>
    <header>
        <h1 onclick="window.location.href='/'">Gestão de Consumo</h1>
        {% if session.get('logado') %}
        <form method="post"><input type="submit" name="logout" value="Logout"></form>
        {% endif %}
    </header>

    <div class="map-container" id="map"></div>

    {% if not session.get("logado") %}
    <div class="form-box">
        <h2>Área Privada</h2>
        <form method="post">
            <label for="id_casa">ID da Casa:</label>
            <input type="text" name="id_casa" required>
            <label for="senha">Código do Proprietário:</label>
            <input type="password" name="senha" required>
            <input type="submit" name="login" value="Entrar">
            <input type="submit" name="cancelar_login" value="Voltar">
        </form>
    </div>
    {% endif %}

    {% if session.get("logado") and consumos %}
    <div class="tabela">
        <h2>Consumos da Casa {{ id_casa }} – Proprietário: {{ nome_proprietario }}</h2>

        <form method="get">
            <input type="hidden" name="id" value="{{ id_casa }}">
            <label for="periodo">Filtrar por Período:</label>
            <select name="periodo">
                <option value="">Todos</option>
                {% for c in consumos %}
                    <option value="{{ c['Período'] }}">{{ c['Período'] }}</option>
                {% endfor %}
            </select>
            <button type="submit">Filtrar</button>
        </form>

        <table>
            <tr>
                <th>Tipo</th><th>Período</th><th>Valor</th><th>Unidade</th><th>Custo (€)</th>
            </tr>
            {% for c in consumos %}
            <tr>
                <td>{{ c["Tipo Consumo"] }}</td>
                <td>{{ c["Período"] }}</td>
                <td>{{ c["Valor"] }}</td>
                <td>{{ c["Unidade"] }}</td>
                <td>{{ c["Custo (€)"] }}</td>
            </tr>
            {% endfor %}
        </table>

        <div class="resumo">
            <h3>Resumo de Custos:</h3>
            <ul>
            {% for tipo, valor in resumo.items() %}
                <li>{{ tipo }}: {{ "%.2f"|format(valor) }} €</li>
            {% endfor %}
                <li><strong>Total: {{ "%.2f"|format(total) }} €</strong></li>
            </ul>
        </div>
    </div>
    {% endif %}

    <footer>Projeto académico — Gestão de consumo residencial</footer>

    <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>
    <script>
        var casas = {{ casas|tojson }};
        var map = L.map("map").setView([38.7, -9.1], 9);

        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
            attribution: "© OpenStreetMap contributors"
        }).addTo(map);

        function corPorCertificado(cert) {
            return {
                "A+": "#00e676", "A": "#66bb6a", "B": "#ffee58", "C": "#ffa726",
                "D": "#ff7043", "E": "#ff5722", "F": "#e53935", "G": "#b71c1c"
            }[cert] || "#999";
        }

        casas.forEach(casa => {
            var marker = L.circleMarker([casa["Latitude"], casa["Longitude"]], {
                radius: 8,
                fillColor: corPorCertificado(casa["Certificado Energético"]),
                color: "#000", weight: 1, opacity: 1,
                fillOpacity: 0.8
            }).addTo(map);

            var info = `<b>${casa["Descrição"]}</b><br>${casa["Morada"]}<br>Certificado: ${casa["Certificado Energético"]}`;
            {% if session.get("logado") %}
            info += `<br><a href='/?id=${casa["ID"]}'>Ver consumos</a>`;
            {% endif %}

            marker.bindPopup(info);
        });
    </script>
</body>
</html>
""", casas=casas, consumos=consumos, resumo=resumo, total=total, id_casa=id_casa, nome_proprietario=nome_proprietario)

if __name__ == "__main__":
    app.run(debug=True)
