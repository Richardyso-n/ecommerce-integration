import pika
import json
import time
import logging
import random

logging.basicConfig(level=logging.INFO)

def callback(ch, method, properties, body):
    pedido = json.loads(body)
    logging.info(f"[Pagamento] Processando pagamento do pedido: {pedido['pedido_id']}")
    
    # Simula processamento
    time.sleep(1)
    resultado = "APROVADO" if random.random() > 0.2 else "REJEITADO"
    
    logging.info(f"[Pagamento] Resultado do pedido {pedido['pedido_id']}: {resultado}")
    ch.basic_ack(delivery_tag=method.delivery_tag)

def main():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
    channel = connection.channel()
    channel.queue_declare(queue='pedido_criado_queue', durable=True)
    
    channel.basic_consume(queue='pedido_criado_queue', on_message_callback=callback)
    logging.info("[Pagamento] Aguardando eventos de novos pedidos...")
    channel.start_consuming()

if __name__ == '__main__':
    main()