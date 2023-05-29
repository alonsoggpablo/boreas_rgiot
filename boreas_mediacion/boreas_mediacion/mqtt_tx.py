import json
import re
import ssl
import paho.mqtt.client as mqtt
import django
import os

import pytz

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "boreas_rgiot.boreas_mediacion.boreas_mediacion.settings")
from django.conf import settings
import psycopg2
from datetime import datetime,timedelta
from django.utils import timezone
django.setup()
from .models import mqtt_msg, reported_measure, MQTT_broker, MQTT_topic

dbHost = settings.DATABASES['default']['HOST']
dbUsername = settings.DATABASES['default']['USER']
dbPassword = settings.DATABASES['default']['PASSWORD']
dbName= settings.DATABASES['default']['NAME']
dbPort= settings.DATABASES['default']['PORT']

conn = psycopg2.connect(
   database=dbName, user=dbUsername , password=dbPassword , host=dbHost, port= dbPort
)
cursor = conn.cursor()


def on_connect(mqtt_client, userdata, flags, rc):

    if rc == 0:
        print('Connected successfully')
        mqtt_client.publish("get/1116587881/command", "wan")
    else:
        print('Bad connection. Code:', rc)
    mqtt_client.disconnect()

def on_publish(client,userdata,result):
    #create function for callback
    print("data published \n")
    print (result)
    print (userdata)
    pass
    return


    # Obtenemos datos del broker mqtt


mqtt_server = MQTT_broker.objects.filter(name='rgiot').values_list('server', flat=True)[0]
mqtt_port = MQTT_broker.objects.filter(name='rgiot').values_list('port', flat=True)[0]
mqtt_keepalive = MQTT_broker.objects.filter(name='rgiot').values_list('keepalive', flat=True)[0]
mqtt_user = MQTT_broker.objects.filter(name='rgiot').values_list('user', flat=True)[0]
mqtt_password = MQTT_broker.objects.filter(name='rgiot').values_list('password', flat=True)[0]

MQTT_SERVER = mqtt_server
MQTT_PORT = mqtt_port
MQTT_KEEPALIVE = mqtt_keepalive
MQTT_USER = mqtt_user
MQTT_PASSWORD = mqtt_password

client = mqtt.Client()
client.on_publish = on_publish
client.on_connect = on_connect
client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
client.tls_set(certfile=None,
                    keyfile=None, cert_reqs=ssl.CERT_NONE,
                    tls_version=ssl.PROTOCOL_TLSv1_2, ciphers=None)
client.connect(
        host=MQTT_SERVER,
        port=MQTT_PORT,
        keepalive=MQTT_KEEPALIVE
    )


