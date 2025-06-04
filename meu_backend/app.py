from flask import Flask, request, jsonify
import paho.mqtt.publish as publish
import json

app = Flask(__name__)

MQTT_BROKER = '0ea2697a3d79439dbfd101a6f7896593.s1.eu.hivemq.cloud'
MQTT_PORT = 8883
MQTT_USER = 'esp32_user'
MQTT_PASS = 'Esp32_pass'
MQTT_TOPIC = 'supabase/comandos'

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    maquina = data.get('maquina')
    comando = data.get('comando')
    tempo = data.get('tempo')

    if not all([maquina, comando, tempo]):
        return jsonify({'status': 'error', 'message': 'Dados incompletos'}), 400

    payload = json.dumps({
        'maquina': maquina,
        'comando': 'VERDADE' if comando else 'FALSO',
        'tempo': tempo
    })

    publish.single(
        MQTT_TOPIC,
        payload,
        hostname=MQTT_BROKER,
        port=MQTT_PORT,
        auth={'username': MQTT_USER, 'password': MQTT_PASS},
        tls={'insecure': True}
    )

    return jsonify({'status': 'success', 'payload': payload}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
