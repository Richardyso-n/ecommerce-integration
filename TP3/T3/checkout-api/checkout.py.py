from flask import Flask, request, jsonify
import requests
import pika
import json
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

ESTOQUE_URL = "http://estoque-service:5001/estoque/verificar"
# Estado simples para simular Circuit Breaker
circuit_breaker_open = False
falhas_consecutivas = 0

def enviar_evento_pedido(pedido):
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
        channel = connection.channel()
        channel.queue_declare(queue='pedido_criado_queue', durable=True)
        
        channel.basic_publish(
            exchange='',
            routing_key='pedido_criado_queue',
            body=json.dumps(pedido),
            properties=pika.BasicProperties(delivery_mode=2)
        )
        connection.close()
        logging.info(f"[Checkout] Evento PedidoCriado enviado para o broker: {pedido['pedido_id']}")
    except Exception as e:
        logging.error(f"[Checkout] Erro ao enviar para o Message Broker: {e}")

@app.route('/pedidos', methods=['POST'])
def criar_pedido():
    global circuit_breaker_open, falhas_consecutivas
    
    if circuit_breaker_open:
        logging.warning("[Circuit Breaker] REQUISIÇÃO RECUSADA IMEDIATAMENTE (Circuito Aberto).")
        return jsonify({"erro": "Serviço temporariamente indisponível (Circuit Breaker)"}), 503

    data = request.get_json()
    
    # 1. Chamada Síncrona ao Estoque
    try:
        response = requests.post(ESTOQUE_URL, json=data, timeout=2)
        falhas_consecutivas = 0 # Reseta falhas se responder
    except Exception:
        falhas_consecutivas += 1
        logging.error(f"[Checkout] Falha ao contatar estoque. Falhas consecutivas: {falhas_consecutivas}")
        if falhas_consecutivas >= 3:
            circuit_breaker_open = True
            logging.error("[Circuit Breaker] CIRCUITO ABERTO!")
        return jsonify({"erro": "Erro de comunicação com o estoque"}), 500

    if response.status_code == 200 and response.json().get("disponivel"):
        # 2. Comunicação Assíncrona via Mensageria
        pedido_id = data.get("pedido_id")
        pedido_evento = {"pedido_id": pedido_id, "cliente": data.get("cliente"), "status": "Criado"}
        
        enviar_evento_pedido(pedido_evento)
        return jsonify({"status": "Pedido recebido com sucesso!", "pedido_id": pedido_id}), 201
    else:
        return jsonify({"erro": "Produto indisponível ou não encontrado no estoque"}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)