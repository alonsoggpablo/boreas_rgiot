import json
import ssl
import paho.mqtt.client as mqtt
import django
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "boreas_rgiot.boreas_mediacion.boreas_mediacion.settings")
from django.conf import settings
import psycopg2

django.setup()
from .models import mqtt_msg, reported_measure

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
class MQTT_device_measure_payload:
    def __init__(self,measure):
        self.measure=measure
    def get_value(self):
        value=self.measure
        return value
class MQTT_device_measure:
    def __init__(self,id,circuit,type,relay):
        self.id = id
        self.circuit = circuit
        self.type = type
        self.relay = relay


    def MQTT_to_dict(self):
        device_dict={}
        device_dict['id']=self.id
        device_dict['circuit']=self.circuit
        device_dict['type']=self.type
        device_dict['relay']=self.relay

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

def max_num_medidas(type):
    if 'shelly' in type:
        max_num_medidas=6
    return max_num_medidas
def message_handler(payload,topic):
    mqtt_dm_topic=MQTT_device_measure_topic(topic)
    mqtt_dm_payload=MQTT_device_measure_payload(payload)

    id=mqtt_dm_topic.get_id()
    circuit=mqtt_dm_topic.get_circuit()
    type=mqtt_dm_topic.get_type()
    relay=mqtt_dm_topic.get_relay()
    parameter=mqtt_dm_topic.get_parameter()
    value=mqtt_dm_payload.get_value()

    mqtt_dm=MQTT_device_measure(id,circuit,type,relay)
    mqtt_dm_dict=mqtt_dm.MQTT_to_dict()
    mqtt_dm_dict['measure'][parameter]=value
    if relay == 'no_relay' or relay=='ext_temperatures' or relay=='announce':
        mqtt_dm_dict['measure']=value

    device=id+'_'+circuit+'_'+type+'_'+relay

    if relay=='relay' or relay == 'no_relay' or relay == 'ext_temperatures' or parameter == 'no_parameter' or relay == 'announce':
        reported_measure(device=mqtt_dm_dict['device'], measures=mqtt_dm_dict['measure']).save()

    if relay == 'emeter':

        try:
            mqtt_msg(device=mqtt_dm_dict['device'],measures=mqtt_dm_dict['measure']).save()
        except:
            update_device_field(mqtt_dm_dict['device'], parameter, value)


def on_connect(mqtt_client, userdata, flags, rc):
    if rc == 0:
        print('Connected successfully')
        mqtt_client.subscribe('shellies/#')
    else:
        print('Bad connection. Code:', rc)
def on_message(mqtt_client, userdata, msg):
    topic=msg.topic
    payload = str(msg.payload.decode("utf-8", "ignore"))
    print(f'Received message on topic: {msg.topic} with payload: {msg.payload}')
    message_handler(payload,topic)


MQTT_SERVER = 'mqtt.rg-iotsolutions.com'
MQTT_PORT = 8883
MQTT_KEEPALIVE = 60
MQTT_USER = 'pablo'
MQTT_PASSWORD = 'pabloDev1234'



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


