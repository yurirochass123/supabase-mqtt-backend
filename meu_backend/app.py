from flask import Flask, request, jsonify
import paho.mqtt.client as mqtt
import ssl
import threading
import time
import os

app = Flask(__name__)

# Configuração MQTT HiveMQ
MQTT_BROKER = '0ea2697a3d79439dbfd101a6f7896593.s1.eu.hivemq.cloud'
MQTT_PORT = 8883
MQTT_TOPIC = 'supabase/controle'
MQTT_USER = 'esp32_user'
MQTT_PASS = 'Esp32_pass'

# Flag para status de conexão MQTT
mqtt_connected = False

# Cria o cliente MQTT
mqtt_client = mqtt.Client()

# Configura autenticação e TLS
mqtt_client.username_pw_set(MQTT_USER, MQTT_PASS)
mqtt_client.tls_set(cert_reqs=ssl.CERT_REQUIRED)

def on_connect(client, userdata, flags, rc):
    global mqtt_connected
    if rc == 0:
        print("MQTT conectado com sucesso!")
        mqtt_connected = True
    else:
        print(f"Falha na conexão MQTT, código {rc}")

def on_disconnect(client, userdata, rc):
    global mqtt_connected
    mqtt_connected = False
    print("MQTT desconectado")

# Define callbacks
mqtt_client.on_connect = on_connect
mqtt_client.on_disconnect = on_disconnect

def mqtt_loop():
    while True:
        mqtt_client.loop()
        time.sleep(0.1)  # pequeno delay para não travar CPU

@app.route('/supabase-webhook', methods=['POST'])
def supabase_webhook():
    data = request.get_json()
    print('Recebido webhook:', data)

    # Exemplo: extrair 'comando' da nova linha (ajuste conforme seu payload)
    comando = data.get('record', {}).get('comando', False)

    if comando:
        if mqtt_connected:
            result, mid = mqtt_client.publish(MQTT_TOPIC, 'liberar')
            print(f'Publicado no MQTT: {MQTT_TOPIC} -> liberar. Resultado: {result}, MID: {mid}')
            return jsonify({'status': 'Publicado'}), 200
        else:
            print("Erro: MQTT não está conectado. Não foi possível publicar.")
            return jsonify({'status': 'Erro: MQTT não conectado'}), 500
    else:
        return jsonify({'status': 'Sem comando'}), 200

@app.route('/')
def home():
    return "Supabase MQTT Bridge rodando!", 200

if __name__ == '__main__':
    # Conecta ao MQTT
    print("Conectando ao broker MQTT...")
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT)

    # Inicia o loop MQTT em thread separada para rodar em background
    mqtt_thread = threading.Thread(target=mqtt_loop)
    mqtt_thread.daemon = True
    mqtt_thread.start()

    # Roda o Flask app
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
