import logging
from flask import Flask, request, jsonify
import paho.mqtt.client as mqtt
import ssl
import time

app = Flask(__name__)

MQTT_BROKER = 'cc94fda87fad405fa0f1137675e147dd.s1.eu.hivemq.cloud'
MQTT_PORT = 8883
MQTT_TOPIC = 'supabase/controle'
MQTT_USER = 'esp32_user'
MQTT_PASS = 'Esp32_pass'

@app.route('/supabase-webhook', methods=['POST'])
def supabase_webhook():
    data = request.get_json(silent=True)
    if not data:
        print('JSON inválido ou vazio recebido no webhook')
        return jsonify({'error': 'JSON inválido ou vazio'}), 400

    print(f'Webhook recebido: {data}')

    if isinstance(data.get('record'), dict):
        record = data['record']
    else:
        record = data  # aceita dados direto no JSON raiz

    maquina = record.get('maquina', 'None')
    comando = record.get('comando', 'None')
    tempo = record.get('tempo', 'None')

    mensagem = f"{maquina}|{comando}|{tempo}"

    try:
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        client.username_pw_set(MQTT_USER, MQTT_PASS)
        client.tls_set(cert_reqs=ssl.CERT_NONE)  # Ajuste para CERT_REQUIRED em produção
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()
        result = client.publish(MQTT_TOPIC, mensagem)
        print(f'Publicado no MQTT: {mensagem} -> Resultado: {result}')
        time.sleep(1)
        client.loop_stop()
        client.disconnect()
    except Exception as e:
        print('Erro ao publicar MQTT:', e)
        return jsonify({'error': 'Erro ao publicar MQTT'}), 500

    return jsonify({'status': 'Publicado'}), 200

@app.route('/')
def home():
    return "Supabase MQTT Bridge rodando!", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
