from flask import Flask, request, jsonify
import pandas as pd

app = Flask(__name__)

LINK_CASAS = "https://docs.google.com/spreadsheets/d/1SKveqiaBaYqyQ5JadM59JKQhd__jodFZfjl78KUGa9w/export?format=csv&gid=0"
LINK_CONSUMOS = "https://docs.google.com/spreadsheets/d/1SKveqiaBaYqyQ5JadM59JKQhd__jodFZfjl78KUGa9w/export?format=csv&gid=634466147"
CHAVE_CORRETA = "123"

def carregar_dados():
    try:
        casas = pd.read_csv(LINK_CASAS)
        consumos = pd.read_csv(LINK_CONSUMOS)

        casas.columns = ["id", "descricao", "morada", "latitude", "longitude", "certificado"]
        consumos.columns = ["id", "tipo", "periodo", "valor", "unidade", "custo"]

        df = pd.merge(consumos, casas, on="id", how="left")
        return df
    except Exception as e:
        print(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()

@app.route("/")
def home():
    return "Projeto 2 - Gestão de Consumos | /resumo | /detalhe?id=1&chave=123"

@app.route("/resumo")
def rota_resumo():
    df = carregar_dados()
    if df.empty:
        return jsonify({"erro": "Não foi possível carregar os dados"}), 500
        
    resumo = df.groupby(['id', 'descricao', 'morada', 'latitude', 'longitude', 'certificado']) \
               .agg(
                   total_consumo=('valor', 'sum'),
                   total_custo=('custo', 'sum'),
                   tipos_consumo=('tipo', lambda x: list(x.unique()))
               ) \
               .reset_index()
    
    return jsonify(resumo.to_dict(orient="records"))

@app.route("/detalhe")
def rota_detalhe():
    id_requisitado = request.args.get("id")
    chave = request.args.get("chave")

    if chave != CHAVE_CORRETA:
        return jsonify({"erro": "Chave de acesso inválida"}), 403

    df = carregar_dados()
    if df.empty:
        return jsonify({"erro": "Não foi possível carregar os dados"}), 500

    dados_filtrados = df[df["id"].astype(str) == str(id_requisitado)]

    if dados_filtrados.empty:
        return jsonify({"erro": "Residência não encontrada"}), 404

    return jsonify(dados_filtrados.to_dict(orient="records"))

if __name__ == "__main__":
    app.run(debug=True)
