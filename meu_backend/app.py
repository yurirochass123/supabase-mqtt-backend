from flask import Flask, request, jsonify
import paho.mqtt.client as mqtt
import ssl
import os
import threading

app = Flask(__name__)

# Configuração MQTT HiveMQ
MQTT_BROKER = '0ea2697a3d79439dbfd101a6f7896593.s1.eu.hivemq.cloud'
MQTT_PORT = 8883
MQTT_TOPIC = 'supabase/controle'
MQTT_USER = 'esp32_user'
MQTT_PASS = 'Esp32_pass'

# Cliente MQTT
mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqtt_client.username_pw_set(MQTT_USER, MQTT_PASS)
mqtt_client.tls_set(cert_reqs=ssl.CERT_REQUIRED)
mqtt_client.connect(MQTT_BROKER, MQTT_PORT)

# Mantém loop em background
def mqtt_loop():
    mqtt_client.loop_forever()

mqtt_thread = threading.Thread(target=mqtt_loop)
mqtt_thread.daemon = True
mqtt_thread.start()

@app.route('/supabase-webhook', methods=['POST'])
def supabase_webhook():
    data = request.get_json()
    print('Webhook recebido:', data)

    record = data.get('record', {})
    maquina = record.get('maquina')
    comando = record.get('comando')
    tempo = record.get('tempo')

    mensagem = f"{maquina}|{comando}|{tempo}"
    result = mqtt_client.publish(MQTT_TOPIC, mensagem)
    
    print(f'Publicado no MQTT: {mensagem} -> Resultado: {result}')
    return jsonify({'status': 'Publicado'}), 200

    
@app.route('/')
def home():
    return "Supabase MQTT Bridge rodando!", 200

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
