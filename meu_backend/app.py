import ssl
import json
import logging
import time
from flask import Flask, request, jsonify
import paho.mqtt.client as mqtt

# Configuração do logging estruturado
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

app = Flask(__name__)

# Controle de duplicidade de eventos
ULTIMOS_EVENTOS = {}
TEMPO_EXPIRACAO_EVENTO = 10  # segundos

# Configurações MQTT
MQTT_BROKER = "0ea2697a3d79439dbfd101a6f7896593.s1.eu.hivemq.cloud"
MQTT_PORT = 8883
MQTT_USER = "esp32_user"
MQTT_PASS = "Esp32_pass"
MQTT_TOPIC = "supabase/controle"

# Cliente MQTT com TLS
mqtt_client = mqtt.Client()
mqtt_client.username_pw_set(MQTT_USER, MQTT_PASS)
mqtt_client.tls_set(cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLS)
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)

# Middleware mTLS
def validar_certificado():
    cert = request.environ.get("SSL_CLIENT_CERT")
    if not cert:
        logging.error("Conexão rejeitada: certificado cliente ausente.")
        return False
    logging.info("Certificado cliente validado com sucesso.")
    return True

@app.route("/supabase-webhook", methods=["POST"])
def receber_webhook():
    if not validar_certificado():
        return jsonify({"erro": "Certificado inválido"}), 403

    try:
        dados = request.get_json(force=True)
    except Exception:
        logging.error("Payload inválido recebido.")
        return jsonify({"erro": "JSON inválido"}), 400

    logging.info(f"Recebido webhook: {dados}")

    # Validação básica
    if not all(k in dados for k in ("maquina", "comando", "tempo")):
        return jsonify({"erro": "Campos ausentes"}), 400

    maquina = dados["maquina"]
    comando = dados["comando"]
    tempo = dados["tempo"]

    # Evita processar evento duplicado
    chave_evento = f"{maquina}-{comando}-{tempo}"
    agora = time.time()

    if chave_evento in ULTIMOS_EVENTOS:
        if agora - ULTIMOS_EVENTOS[chave_evento] < TEMPO_EXPIRACAO_EVENTO:
            logging.warning(f"Evento duplicado ignorado: {chave_evento}")
            return jsonify({"status": "ignorado"}), 200

    ULTIMOS_EVENTOS[chave_evento] = agora

    # Publica no MQTT
    try:
        payload_mqtt = f"{maquina}|{int(comando)}|{tempo}"
        mqtt_client.publish(MQTT_TOPIC, payload_mqtt)
        logging.info(f"Comando enviado via MQTT: {payload_mqtt}")
    except Exception as e:
        logging.error(f"Falha ao publicar no MQTT: {e}")
        return jsonify({"erro": "Falha MQTT"}), 500

    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(certfile="server.crt", keyfile="server.key")
    context.load_verify_locations(cafile="ca.crt")
    context.verify_mode = ssl.CERT_REQUIRED

    app.run(host="0.0.0.0", port=443, ssl_context=context)
