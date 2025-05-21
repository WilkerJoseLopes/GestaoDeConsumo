from flask import Flask, request, jsonify
import pandas as pd

app = Flask(__name__)

# Links diretos para CSV das folhas do Google Sheets
LINK_CASAS = "https://docs.google.com/spreadsheets/d/1SKveqiaBaYqyQ5JadM59JKQhd__jodFZfjl78KUGa9w/edit?gid=0#gid=0"
LINK_CONSUMOS = "https://docs.google.com/spreadsheets/d/1SKveqiaBaYqyQ5JadM59JKQhd__jodFZfjl78KUGa9w/edit?gid=634466147#gid=634466147"
CHAVE_CORRETA = "123"

def carregar_dados():
    casas = pd.read_csv(LINK_CASAS)
    consumos = pd.read_csv(LINK_CONSUMOS)

    casas.columns = ["id", "descricao", "morada", "certificado"]
    consumos.columns = ["id", "localizacao", "tipo", "periodo", "valor", "unidade", "custo"]

    df = pd.merge(consumos, casas, on="id", how="left")
    return df

@app.route("/")
def home():
    return "Projeto 2 - Gestão de Consumos | /resumo | /detalhe?id=1&chave=123"

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

