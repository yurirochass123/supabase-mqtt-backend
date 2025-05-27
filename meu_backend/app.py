from flask import Flask, request, jsonify
import paho.mqtt.client as mqtt
import ssl
import os

app = Flask(__name__)

MQTT_BROKER = '0ea2697a3d79439dbfd101a6f7896593.s1.eu.hivemq.cloud'
MQTT_PORT = 8883
MQTT_TOPIC = 'supabase/controle'
MQTT_USER = 'esp32_user'
MQTT_PASS = 'Esp32_pass'

mqtt_client = mqtt.Client()
mqtt_client.username_pw_set(MQTT_USER, MQTT_PASS)
mqtt_client.tls_set(cert_reqs=ssl.CERT_NONE)  # para evitar problema com certificado
mqtt_client.tls_insecure_set(True)
mqtt_client.connect(MQTT_BROKER, MQTT_PORT)
mqtt_client.loop_start()  # ESSENCIAL: mantém conexão MQTT ativa

@app.route('/supabase-webhook', methods=['POST'])
def supabase_webhook():
    data = request.get_json()
    print('Recebido webhook:', data)

    # Depende do formato recebido:
    # Pode ser em 'record' ou 'new' (de acordo com seu log)
    comando = data.get('record', {}).get('comando', False)

    print(f'Comando extraído: {comando}')

    if comando:
        result = mqtt_client.publish(MQTT_TOPIC, 'liberar')
        print(f'Publicado no MQTT: {MQTT_TOPIC} -> liberar, resultado: {result}')
        return jsonify({'status': 'Publicado'}), 200
    else:
        return jsonify({'status': 'Sem comando'}), 200

@app.route('/')
def home():
    return "Supabase MQTT Bridge rodando!", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
