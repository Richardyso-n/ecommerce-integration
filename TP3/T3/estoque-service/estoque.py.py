from flask import Flask, jsonify, request
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Mock de estoque em memória
ESTOQUE = {"produto_A": 10, "produto_B": 5, "produto_C": 0}

@app.route('/estoque/verificar', methods=['POST'])
def verificar_estoque():
    data = request.get_json()
    produto_id = data.get("produto_id")
    quantidade = data.get("quantidade", 1)
    
    logging.info(f"[Estoque] Verificando {quantidade} unidades do produto {produto_id}")
    
    if produto_id not in ESTOQUE:
        return jsonify({"disponivel": False, "erro": "Produto não encontrado"}), 404
        
    if ESTOQUE[produto_id] >= quantidade:
        return jsonify({"disponivel": True}), 200
    else:
        return jsonify({"disponivel": False, "erro": "Saldo insuficiente"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)