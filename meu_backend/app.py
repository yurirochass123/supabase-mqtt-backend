import logging
from flask import Flask, request, jsonify
import paho.mqtt.client as mqtt
import ssl
import os
import threading

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MQTT_BROKER = 'cc94fda87fad405fa0f1137675e147dd.s1.eu.hivemq.cloud'
MQTT_PORT = 8883
MQTT_TOPIC = 'supabase/controle'
MQTT_USER = 'esp32_user'
MQTT_PASS = 'Esp32_pass'

mqtt_client = mqtt.Client()
mqtt_client.username_pw_set(MQTT_USER, MQTT_PASS)
mqtt_client.tls_set()
mqtt_client.connect(MQTT_BROKER, MQTT_PORT)

def mqtt_loop():
    mqtt_client.loop_forever()

mqtt_thread = threading.Thread(target=mqtt_loop)
mqtt_thread.daemon = True
mqtt_thread.start()

@app.route('/supabase-webhook', methods=['POST'])
def supabase_webhook():
    data = request.get_json(silent=True)
    if not data:
        logger.error('JSON inválido ou vazio no webhook')
        return jsonify({'error': 'JSON inválido ou vazio'}), 400

    logger.info(f'Webhook recebido: {data}')
    record = data.get('record')
    if not isinstance(record, dict):
        logger.error('Campo "record" inválido ou ausente')
        return jsonify({'error': 'Campo "record" inválido ou ausente'}), 400

    maquina = record.get('maquina', "None")
    comando = record.get('comando', "None")
    tempo = record.get('tempo', "None")

    mensagem = f"{maquina}|{comando}|{tempo}"
    result = mqtt_client.publish(MQTT_TOPIC, mensagem)
    if result.rc != mqtt.MQTT_ERR_SUCCESS:
        logger.error(f'Erro ao publicar MQTT: {result}')
        return jsonify({'error': 'Falha ao publicar MQTT'}), 500

    logger.info(f'Publicado no MQTT: {mensagem}')
    return jsonify({'status': 'Publicado'}), 200

@app.route('/')
def home():
    return "Supabase MQTT Bridge rodando!", 200

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
