from flask import Flask, request, jsonify
import pandas as pd

app = Flask(__name__)

CAMINHO_EXCEL = "fonte/Gestão de consumos de água, energia e gás.xlsx"
CHAVE_CORRETA = "123"

def carregar_dados():
    # Lê as duas folhas
    casas = pd.read_excel(CAMINHO_EXCEL, sheet_name=0)
    consumos = pd.read_excel(CAMINHO_EXCEL, sheet_name=1)

    # Renomeia colunas para consistência
    casas.columns = ["id", "descricao", "morada", "certificado"]
    consumos.columns = ["id", "localizacao", "tipo", "periodo", "valor", "unidade", "custo"]

    # Junta os dados pelo ID
    df = pd.merge(consumos, casas, on="id", how="left")
    return df

@app.route("/")
def home():
    return "🌐 Projeto 2 - Gestão de Consumos | Rotas: /resumo, /detalhe?id=&chave="

@app.route("/resumo")
def rota_resumo():
    df = carregar_dados()
    resumo = df.groupby(['id', 'descricao', 'morada', 'certificado']) \
               .agg(total_consumo=('valor', 'sum'), total_custo=('custo', 'sum')) \
               .reset_index()
    return jsonify(resumo.to_dict(orient="records"))

@app.route("/detalhe")
def rota_detalhe():
    id_requisitado = request.args.get("id")
    chave = request.args.get("chave")

    if chave != CHAVE_CORRETA:
        return jsonify({"erro": "Chave de acesso inválida"}), 403

    df = carregar_dados()
    dados_filtrados = df[df["id"].astype(str) == str(id_requisitado)]

    if dados_filtrados.empty:
        return jsonify({"erro": "Residência não encontrada"}), 404

    return jsonify(dados_filtrados.to_dict(orient="records"))

if __name__ == "__main__":
    app.run(debug=True)
