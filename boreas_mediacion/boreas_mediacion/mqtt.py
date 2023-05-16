import json
import ssl
import paho.mqtt.client as mqtt
from django.conf import settings
from .models import mqtt_msg

import sqlite3

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
        except:parameter=''
        return parameter

    def get_type(self):
        type=self.topic.split("/")[1].split("-")[0]
        return type

    def get_relay(self):
        relay=self.topic.split("/")[2]
        return relay
class MQTT_device_measure_payload:
    def __init__(self,measure):
        self.measure=measure
    def get_value(self):
        value=self.measure
        return value
class MQTT_device_measure:
    def __init__(self,id,circuit,type,relay,energy,returned_energy,power,pf,current,voltage,total,total_returned):
        self.id = id
        self.circuit = circuit
        self.type = type
        self.relay = relay
        self.energy=energy
        self.returned_energy=returned_energy
        self.power=power
        self.pf=pf
        self.current=current
        self.voltage=voltage
        self.total=total
        self.total_returned=total_returned

    def MQTT_to_dict(self):
        device_dict={}
        device_dict['id']=self.id
        device_dict['circuit']=self.circuit
        device_dict['type']=self.type
        device_dict['relay']=self.relay

        measure_dict={}
        measure_dict['energy']=self.energy
        measure_dict['returned_energy']=self.returned_energy
        measure_dict['power']=self.power
        measure_dict['pf']=self.pf
        measure_dict['current']=self.current
        measure_dict['voltage']=self.voltage
        measure_dict['total']=self.total
        measure_dict['total_returned']=self.total_returned

        device_measure={}
        device_measure['device']=device_dict
        device_measure['measure']=measure_dict

        # json_device_measure=json.dumps(device_measure)

        # return json_device_measure
        return device_measure


def dict_to_json_file(dict,device):
    with open(device+'.json','w') as outfile:
        json.dump(dict,outfile)

def message_handler(payload,topic):
    mqtt_dm_topic=MQTT_device_measure_topic(topic)
    mqtt_dm_payload=MQTT_device_measure_payload(payload)

    id=mqtt_dm_topic.get_id()
    circuit=mqtt_dm_topic.get_circuit()
    type=mqtt_dm_topic.get_type()
    relay=mqtt_dm_topic.get_relay()
    parameter=mqtt_dm_topic.get_parameter()
    value=mqtt_dm_payload.get_value()

    mqtt_dm=MQTT_device_measure(id,circuit,type,relay,"","","","","","","","")
    mqtt_dm_dict=mqtt_dm.MQTT_to_dict()
    if relay=='emeter':
        mqtt_dm_dict['measure'][parameter]=value

    print (mqtt_dm_dict)

    device=id+'_'+circuit+'_'+type+'_'+relay
    dict_to_json_file(mqtt_dm_dict,device)


def on_connect(mqtt_client, userdata, flags, rc):
    if rc == 0:
        print('Connected successfully')
        mqtt_client.subscribe('shellies/#')
    else:
        print('Bad connection. Code:', rc)


def on_message(mqtt_client, userdata, msg):
    topic=msg.topic
    payload = str(msg.payload.decode("utf-8", "ignore"))
    # print('Received message on topic: {msg.topic} with payload: {msg.payload}')
    message_handler(payload,topic)




# MQTT_SERVER = 'mqtt.rg-iotsolutions.com'
# MQTT_PORT = 8883
# MQTT_KEEPALIVE = 60
# MQTT_USER = 'pablo'
# MQTT_PASSWORD = 'pabloDev1234'
# # MQTT_TLS=r'C:\Users\alons\OneDrive\PROYECTOS\RGIoT\isrg-root-x1-cross-signed.pem'
#
# client = mqtt.Client()
# client.on_connect = on_connect
# client.on_message = on_message
# client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
# client.tls_set(ca_certs=MQTT_TLS, certfile=None,
#                     keyfile=None, cert_reqs=ssl.CERT_NONE,
#                     tls_version=ssl.PROTOCOL_TLSv1_2, ciphers=None)
# client.connect(
#     host=MQTT_SERVER,
#     port=MQTT_PORT,
#     keepalive=MQTT_KEEPALIVE
# )