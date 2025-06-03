import os
import pygsheets
from flask import Flask, request, redirect, jsonify
from datetime import datetime
from io import StringIO

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'segredo-default')

# Configuração do Google Sheets
SPREADSHEET_ID = "1SKveqiaBaYqyQ5JadM59JKQhd__jodFZfjl78KUGa9w"
SHEET_NAME = "Dados"

# Autenticação simplificada com tratamento robusto
def get_sheet():
    try:
        gc = pygsheets.authorize(service_account_env_var='GOOGLE_CREDENTIALS')
        sh = gc.open_by_key(SPREADSHEET_ID)
        return sh.worksheet_by_title(SHEET_NAME)
    except Exception as e:
        print(f"ERRO: {str(e)}")
        return None

# HTML embutido diretamente no código
HTML_BASE = """
<!DOCTYPE html>
<html>
<head>
    <title>Gestão de Consumo</title>
    <style>
        body { font-family: Arial; max-width: 800px; margin: 0 auto; padding: 20px; }
        table { width: 100%; border-collapse: collapse; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        tr:nth-child(even) { background-color: #f2f2f2; }
        .alert { padding: 10px; margin: 10px 0; border-radius: 4px; }
        .success { background-color: #dff0d8; color: #3c763d; }
        .error { background-color: #f2dede; color: #a94442; }
    </style>
</head>
<body>
    <h1>Gestão de Consumo</h1>
    {% if mensagem %}<div class="alert {{ mensagem.tipo }}">{{ mensagem.texto }}</div>{% endif %}
    %s
</body>
</html>
"""

HTML_FORM = """
<form method="POST" action="/add">
    <h2>Adicionar Registro</h2>
    <input type="date" name="data" required placeholder="Data">
    <input type="text" name="item" required placeholder="Item">
    <input type="number" step="0.01" name="valor" required placeholder="Valor">
    <input type="text" name="categoria" required placeholder="Categoria">
    <button type="submit">Salvar</button>
</form>
"""

# Rotas principais
@app.route('/')
def dashboard():
    sheet = get_sheet()
    if not sheet:
        return HTML_BASE % "<h2>Erro: Não foi possível conectar ao Google Sheets</h2>"
    
    try:
        registros = sheet.get_all_records()
        # Processamento em memória
        total = sum(float(r.get('Valor', 0)) for r in registros)
        
        # Gerar HTML dinamicamente
        table_rows = []
        for r in registros[-10:]:  # Últimos 10 registros
            table_rows.append(f"""
            <tr>
                <td>{r.get('Data', '')}</td>
                <td>{r.get('Item', '')}</td>
                <td>R$ {float(r.get('Valor', 0)):.2f}</td>
                <td>{r.get('Categoria', '')}</td>
            </tr>
            """)
        
        content = f"""
        <h2>Total: R$ {total:.2f}</h2>
        <table>
            <tr><th>Data</th><th>Item</th><th>Valor</th><th>Categoria</th></tr>
            {''.join(table_rows)}
        </table>
        {HTML_FORM}
        """
        return HTML_BASE % content
        
    except Exception as e:
        return HTML_BASE % f"<h2>Erro ao processar dados: {str(e)}</h2>"

@app.route('/add', methods=['POST'])
def add_registro():
    sheet = get_sheet()
    if not sheet:
        return redirect('/?erro=Conexão+com+planilha+indisponível')
    
    try:
        novo_registro = [
            request.form['data'],
            request.form['item'],
            float(request.form['valor']),
            request.form['categoria'],
            datetime.now().strftime("%d/%m/%Y %H:%M")
        ]
        sheet.append_table(values=novo_registro)
        return redirect('/?sucesso=Registro+adicionado')
    except Exception as e:
        return redirect(f'/?erro={str(e)}')

# API simplificada
@app.route('/api/data')
def api_data():
    sheet = get_sheet()
    if not sheet:
        return jsonify({"error": "Sheet connection failed"}), 500
    
    registros = sheet.get_all_records()
    return jsonify({
        "data": [
            {
                "data": r.get('Data'),
                "valor": float(r.get('Valor', 0)),
                "categoria": r.get('Categoria')
            } for r in registros
        ]
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
