import ssl
import paho.mqtt.client as mqtt
from django.conf import settings


def on_connect(mqtt_client, userdata, flags, rc):
    if rc == 0:
        print('Connected successfully')
        # mqtt_client.subscribe('django/mqtt')
        mqtt_client.subscribe('shellies/#')
    else:
        print('Bad connection. Code:', rc)


def on_message(mqtt_client, userdata, msg):
    print(f'Received message on topic: {msg.topic} with payload: {msg.payload}')


MQTT_SERVER = 'mqtt.rg-iotsolutions.com'
MQTT_PORT = 8883
MQTT_KEEPALIVE = 60
MQTT_USER = 'pablo'
MQTT_PASSWORD = 'pabloDev1234'
MQTT_TLS=r'C:\Users\alons\OneDrive\PROYECTOS\RGIoT\isrg-root-x1-cross-signed.pem'

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
# client.tls_set(ca_certs=MQTT_TLS)
client.tls_set(ca_certs=MQTT_TLS, certfile=None,
                    keyfile=None, cert_reqs=ssl.CERT_NONE,
                    tls_version=ssl.PROTOCOL_TLSv1_2, ciphers=None)
# client.tls_insecure_set(True)
client.connect(
    host=MQTT_SERVER,
    port=MQTT_PORT,
    keepalive=MQTT_KEEPALIVE
)