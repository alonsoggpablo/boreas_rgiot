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



class MQTT_device_measure_topic:
    def __init__(self,topic):
        self.topic=topic
    def get_id(self):
        id=self.topic.split("/")[1]
        return id

    def get_circuit(self):
        try:
            circuit=self.topic.split("/")[3]
        except:circuit=''
        return circuit

    def get_parameter(self):
        try:
            parameter=self.topic.split("/")[4]
        except:
            if ('relay' in self.get_relay()) or ('temp' in self.get_relay()):
                parameter=self.get_relay()
            else: parameter='no_parameter'
        return parameter

    def get_type(self):
        type=self.topic.split("/")[1].split("-")[0]
        return type

    def get_relay(self):

        try:
            relay=self.topic.split("/")[2]
        except:relay='no_relay'

        return relay

    def get_feed(self):
        try:
            feed=self.topic.split("/")[0]
        except:feed='no_feed'
        return feed
class MQTT_device_measure_payload:
    def __init__(self,measure):
        self.measure=measure
    def get_value(self):
        value=self.measure
        return value
class MQTT_device_measure:
    def __init__(self,id,circuit,type,relay,feed):
        self.id = id
        self.circuit = circuit
        self.type = type
        self.relay = relay
        self.feed = feed


    def MQTT_to_dict(self):
        device_dict={}
        device_dict['id']=self.id
        device_dict['circuit']=self.circuit
        device_dict['type']=self.type
        device_dict['relay']=self.relay
        device_dict['feed']=self.feed

        measure_dict={}

        device_measure={}
        device_measure['device']=device_dict
        device_measure['measure']=measure_dict

        return device_measure

def dict_to_json_file(dict,device):
    with open(device+'.json','w') as outfile:
        json.dump(dict,outfile)
def update_device_field(device,field,field_value):
    field_dict={}
    field_dict[field]=field_value
    field_dict_str=str(field_dict).replace("'",'"')
    device_str=str(device).replace("'",'"')
    query = f"""update boreas_mediacion_mqtt_msg set report_time=now(),measures=measures ||'{field_dict_str}' where device= '{device_str}' """.replace("\\","")
    cursor.execute(query=query)
    conn.commit()


    return

def find_pattern(pattern, string):
    match = re.search(pattern, string)
    return match.group() if match else None

def message_handler(payload,topic):
    mqtt_dm_topic=MQTT_device_measure_topic(topic)
    mqtt_dm_payload=MQTT_device_measure_payload(payload)

    id=mqtt_dm_topic.get_id()
    circuit=mqtt_dm_topic.get_circuit()
    type=mqtt_dm_topic.get_type()
    relay=mqtt_dm_topic.get_relay()
    parameter=mqtt_dm_topic.get_parameter()
    feed=mqtt_dm_topic.get_feed()
    value=mqtt_dm_payload.get_value()

    mqtt_dm=MQTT_device_measure(id,circuit,type,relay,feed)
    mqtt_dm_dict=mqtt_dm.MQTT_to_dict()
    mqtt_dm_dict['measure'][parameter]=value

    if feed=='shellies':

        if relay == 'no_relay' or relay=='ext_temperatures' or relay=='announce':
            mqtt_dm_dict['measure']=value

        device=id+'_'+circuit+'_'+type+'_'+relay

        if relay=='relay' or relay == 'no_relay' or relay == 'ext_temperatures' or parameter == 'no_parameter' or relay == 'announce':
            reported_measure(device=mqtt_dm_dict['device'], measures=mqtt_dm_dict['measure'],device_id=id,feed=feed).save()
            try:
                reported_measure.objects.filter(device=mqtt_dm_dict['device'],report_time__lt=timezone.now()-timedelta(minutes=5)).delete()
            except:pass

        if relay == 'emeter':

            try:
                mqtt_msg(device=mqtt_dm_dict['device'],measures=mqtt_dm_dict['measure'],device_id=id,feed=feed).save()
            except:
                update_device_field(mqtt_dm_dict['device'], parameter, value)

    else:
        device_id = ((find_pattern(r'/(?:(?!/).)+-(?:(?!/).)', mqtt_dm_topic.topic) or
                      json.loads(mqtt_dm_payload.measure)['device']['id']) or 'no_device_id').strip("/")

        if mqtt_msg.objects.filter(device=mqtt_dm_topic.topic+'_'+device_id).exists():
            mqtt_msg.objects.filter(device=mqtt_dm_topic.topic+'_'+device_id).update(measures=mqtt_dm_payload.measure,report_time=timezone.now())
        else:
            try:


                mqtt_msg(device=mqtt_dm_topic.topic+'_'+device_id,measures=mqtt_dm_payload.measure,device_id=device_id,feed=feed).save()
            except:
                pass
def get_topics_list():
    topics_list= list(zip(MQTT_topic.objects.filter(active=True).values_list('topic',flat=True),MQTT_topic.objects.filter(active=True).values_list('qos',flat=True)))
    return topics_list

get_topics_list()

def on_connect(mqtt_client, userdata, flags, rc):

    if rc == 0:
        print('Connected successfully')
        # mqtt_client.subscribe('shellies/#')
        # mqtt_client.subscribe([('RESP/tactica/#',0),('shellies/#',0)])
        mqtt_client.subscribe(get_topics_list())
        # mqtt_client.subscribe(get_topics_list())
    else:
        print('Bad connection. Code:', rc)
def on_message(mqtt_client, userdata, msg):
    topic=msg.topic
    payload = str(msg.payload.decode("utf-8", "ignore"))
    print(f'Received message on topic: {msg.topic} with payload: {msg.payload}')
    message_handler(payload,topic)

#Obtenemos datos del broker mqtt
mqtt_server=MQTT_broker.objects.filter(name='rgiot').values_list('server',flat=True)[0]
mqtt_port=MQTT_broker.objects.filter(name='rgiot').values_list('port',flat=True)[0]
mqtt_keepalive=MQTT_broker.objects.filter(name='rgiot').values_list('keepalive',flat=True)[0]
mqtt_user=MQTT_broker.objects.filter(name='rgiot').values_list('user',flat=True)[0]
mqtt_password=MQTT_broker.objects.filter(name='rgiot').values_list('password',flat=True)[0]

MQTT_SERVER = mqtt_server
MQTT_PORT = mqtt_port
MQTT_KEEPALIVE = mqtt_keepalive
MQTT_USER = mqtt_user
MQTT_PASSWORD = mqtt_password


# MQTT_SERVER = 'mqtt.rg-iotsolutions.com'
# MQTT_PORT = 8883
# MQTT_KEEPALIVE = 60
# MQTT_USER = 'pablo'
# MQTT_PASSWORD = 'pabloDev1234'



client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
client.tls_set(certfile=None,
                    keyfile=None, cert_reqs=ssl.CERT_NONE,
                    tls_version=ssl.PROTOCOL_TLSv1_2, ciphers=None)
client.connect(
    host=MQTT_SERVER,
    port=MQTT_PORT,
    keepalive=MQTT_KEEPALIVE
)


