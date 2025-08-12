from flask import Flask, request, jsonify
import paho.mqtt.client as mqtt
import ssl
import os
import threading
import time
import logging

# ===== CONFIG LOGS =====
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuração MQTT HiveMQ
MQTT_BROKER = '0ea2697a3d79439dbfd101a6f7896593.s1.eu.hivemq.cloud'
MQTT_PORT = 8883
MQTT_TOPIC = 'supabase/controle'
MQTT_USER = 'esp32_user'
MQTT_PASS = 'Esp32_pass'

# Cliente MQTT
mqtt_client = mqtt.Client()
mqtt_client.username_pw_set(MQTT_USER, MQTT_PASS)
mqtt_client.tls_set()  # usa certificado CA do sistema

# ===== CALLBACKS =====
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logger.info("✅ Conectado ao broker MQTT!")
    else:
        logger.error(f"❌ Falha na conexão MQTT. Código: {rc}")

def on_disconnect(client, userdata, rc):
    logger.warning(f"⚠ Desconectado do broker MQTT (rc={rc}). Tentando reconectar...")
    reconnect_mqtt()

mqtt_client.on_connect = on_connect
mqtt_client.on_disconnect = on_disconnect

# ===== RECONEXÃO =====
def reconnect_mqtt():
    while True:
        try:
            mqtt_client.connect(MQTT_BROKER, MQTT_PORT)
            logger.info("🔄 Reconexão ao broker MQTT bem-sucedida!")
            break
        except Exception as e:
            logger.error(f"Erro ao reconectar: {e}")
            time.sleep(5)

# ===== LOOP EM THREAD =====
def mqtt_loop():
    while True:
        try:
            mqtt_client.loop_forever()
        except Exception as e:
            logger.error(f"Erro no loop MQTT: {e}")
            reconnect_mqtt()

# Conecta inicialmente
reconnect_mqtt()

mqtt_thread = threading.Thread(target=mqtt_loop)
mqtt_thread.daemon = True
mqtt_thread.start()

@app.route('/supabase-webhook', methods=['POST'])
def supabase_webhook():
    try:
        data = request.get_json(force=True)
    except Exception as e:
        logger.error(f"Erro ao ler JSON: {e}")
        return jsonify({'error': 'JSON inválido'}), 400

    if not isinstance(data, dict):
        logger.warning(f"Formato incorreto recebido: {data}")
        return jsonify({'error': 'Payload inválido'}), 400

    maquina = str(data.get('maquina', "None"))
    comando = str(data.get('comando', "None"))
    tempo = str(data.get('tempo', "None"))

    mensagem = f"{maquina}|{comando}|{tempo}"
    
    try:
        result = mqtt_client.publish(MQTT_TOPIC, mensagem)
        logger.info(f"📤 Publicado no MQTT: {mensagem} -> Resultado: {result.rc}")
        return jsonify({'status': 'Publicado'}), 200
    except Exception as e:
        logger.error(f"Erro ao publicar no MQTT: {e}")
        return jsonify({'error': 'Falha ao publicar no MQTT'}), 500

@app.route('/')
def home():
    return "Supabase MQTT Bridge rodando!", 200

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
