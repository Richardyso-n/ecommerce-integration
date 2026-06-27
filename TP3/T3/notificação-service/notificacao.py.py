import pika
import json
import logging

logging.basicConfig(level=logging.INFO)

def callback(ch, method, properties, body):
    pedido = json.loads(body)
    logging.info(f"[Notificação] Processando envio de notificação para o pedido: {pedido['pedido_id']}")
    
    try:
        # Simulação de erro intencional caso o ID seja '999' para forçar DLQ
        if pedido['pedido_id'] == '999':
            raise ValueError("Erro simulado no serviço de e-mail.")
            
        logging.info(f"[Notificação] Sucesso: E-mail de confirmação enviado para {pedido.get('cliente')}")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        
    except Exception as e:
        logging.error(f"[Notificação] Erro no processamento. Movendo para a DLQ. Motivo: {e}")
        # Rejeita e envia explicitamente para a DLQ configurada no RabbitMQ
        ch.basic_reject(delivery_tag=method.delivery_tag, requeue=False)

def main():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
    channel = connection.channel()
    
    # Configura DLQ
    channel.exchange_declare(exchange='dlx_exchange', exchange_type='direct')
    channel.queue_declare(queue='notificacao_dlq', durable=True)
    channel.queue_bind(exchange='dlx_exchange', queue='notificacao_dlq', routing_key='notificacao_mortas')
    
    # Fila Principal vinculada à DLX
    args = {
        'x-dead-letter-exchange': 'dlx_exchange',
        'x-dead-letter-routing-key': 'notificacao_mortas'
    }
    channel.queue_declare(queue='pedido_criado_queue', durable=True, arguments=args)
    
    channel.basic_consume(queue='pedido_criado_queue', on_message_callback=callback)
    logging.info("[Notificação] Aguardando eventos para envio de notificações...")
    channel.start_consuming()

if __name__ == '__main__':
    main()