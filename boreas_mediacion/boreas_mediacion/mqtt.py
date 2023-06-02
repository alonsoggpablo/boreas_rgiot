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
from .models import mqtt_msg, reported_measure, MQTT_broker, MQTT_topic, MQTT_tx, MQTT_feed

dbHost = settings.DATABASES['default']['HOST']
dbUsername = settings.DATABASES['default']['USER']
dbPassword = settings.DATABASES['default']['PASSWORD']
dbName= settings.DATABASES['default']['NAME']
dbPort= settings.DATABASES['default']['PORT']

conn = psycopg2.connect(
   database=dbName, user=dbUsername , password=dbPassword , host=dbHost, port= dbPort
)
cursor = conn.cursor()

from django.db.models.signals import post_save
from django.dispatch import receiver

class MQTT_msg_topic:
    def __init__(self,topic):
        self.topic=topic
    def get_0(self):
        try:
            topic_0=self.topic.split("/")[0]
        except:topic_0=''
        return topic_0
    def get_1(self):
        try:
            topic_1=self.topic.split("/")[1]
        except:topic_1=''
        return topic_1
    def get_2(self):
        try:
            topic_2=self.topic.split("/")[2]
        except:topic_2=''
        return topic_2
    def get_3(self):
        try:
            topic_3=self.topic.split("/")[3]
        except:topic_3=''
        return topic_3
    def get_4(self):
        try:
            topic_4=self.topic.split("/")[4]
        except:topic_4=''
        return topic_4
    def get_5(self):
        try:
            topic_5=self.topic.split("/")[5]
        except:topic_5=''
        return topic_5
class MQTT_msg_payload:
    def __init__(self,payload):
        self.payload=payload
    def get_0(self):
        try:
            payload_0=self.payload.split("/")[0]
        except:payload_0=''
        return payload_0
class MQTT_msg_topic_payload_dict:
    def __init__(self,topic_0,topic_1,topic_2,topic_3,topic_4,topic_5,payload_0):
        self.topic_0=topic_0
        self.topic_1=topic_1
        self.topic_2=topic_2
        self.topic_3=topic_3
        self.topic_4=topic_4
        self.topic_5=topic_5
        self.payload_0=payload_0

    def MQTT_to_dict(self):
        topic_dict={}
        topic_dict['0']=self.topic_0
        topic_dict['1']=self.topic_1
        topic_dict['2']=self.topic_2
        topic_dict['3']=self.topic_3
        topic_dict['4']=self.topic_4
        topic_dict['5']=self.topic_5
        payload_dict={}
        payload_dict['0']=self.payload_0
        topic_payload_dict={}
        topic_payload_dict['topic']=topic_dict
        topic_payload_dict['payload']=payload_dict
        return topic_payload_dict



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

def sensor_message_handler(payload,topic):
    mqtt_dm_topic=MQTT_msg_topic(topic)
    mqtt_dm_payload=MQTT_msg_payload(payload)

    id=mqtt_dm_topic.get_1()
    circuit=mqtt_dm_topic.get_3()
    type=mqtt_dm_topic.get_1().split("-")[0]
    relay=mqtt_dm_topic.get_2()
    parameter=mqtt_dm_topic.get_4()
    feed=mqtt_dm_topic.get_0()
    value=mqtt_dm_payload.get_0()

    mqtt_dm=MQTT_device_measure(id,circuit,type,relay,feed)
    mqtt_dm_dict=mqtt_dm.MQTT_to_dict()
    mqtt_dm_dict['measure'][parameter]=value

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


    if parameter=='total_returned':
        params=mqtt_msg.objects.filter(device_id=id).values_list('measures',flat=True)[0]
        payload_dict=str({'device':{'id':id,'circuit':circuit,'type':type,'relay':relay},'measures':params})
        topic=MQTT_feed.objects.filter(name=feed).values_list('topic__topic',flat=True)[0].strip('/#')
        MQTT_tx(topic=topic,payload=payload_dict).save()

def general_message_handler(payload,topic):
    mqtt_dm_topic = MQTT_device_measure_topic(topic)
    mqtt_dm_payload = MQTT_device_measure_payload(payload)
    try:
        mqtt_msg(device=mqtt_dm_topic.topic, measures=mqtt_dm_payload.measure).save()
    except:
        mqtt_msg.objects.filter(device=mqtt_dm_topic.topic).update(device=mqtt_dm_topic.topic, measures=mqtt_dm_payload.measure, report_time=timezone.now())


def router_message_handler(payload,topic):

    mqtt_dm_topic=MQTT_msg_topic(topic)
    mqtt_dm_payload=MQTT_msg_payload(payload)
    feed = mqtt_dm_topic.get_0()
    device_id = mqtt_dm_topic.get_1()
    parameter=mqtt_dm_topic.get_2()
    value=mqtt_dm_payload.get_0()
    if parameter=='uptime':
        value=str(format(int(value)/3600,'.2f'))
    if parameter=='temperature':
        try:
            value=str(float(value)/10)
        except:value=value

    measure={parameter:value}
    device={'id':device_id}
    if mqtt_msg.objects.filter(device_id=device_id).exists():
        update_device_field(device, parameter, value)
    else:
        try:

            mqtt_msg(device=device, measures=measure,
                     device_id=device_id, feed=feed).save()
        except:
            pass

    if parameter=='name':
        params=mqtt_msg.objects.filter(device_id=device_id).values_list('measures',flat=True)[0]
        payload_dict=str({'device':{'id':device_id,'model':value},'params':params})
        topic=MQTT_feed.objects.filter(name=feed).values_list('topic__topic',flat=True)[0].strip('/#')
        MQTT_tx(topic=topic,payload=payload_dict).save()

def router_report_message_handler(payload,topic):

    mqtt_dm_topic=MQTT_msg_topic(topic)
    mqtt_dm_payload=MQTT_msg_payload(payload)
    feed = mqtt_dm_topic.get_0()
    device=json.loads(payload.replace("'",'"'))['device']
    device_id = device['id']
    measures=json.loads(payload.replace("'",'"'))['params']

    if mqtt_msg.objects.filter(device=device).exists():
        mqtt_msg.objects.filter(device=device).update(measures=measures, report_time=timezone.now())
    else:
        try:

            mqtt_msg(device=device, measures=measures,
                     device_id=device_id, feed=feed).save()
        except:
            pass
def sensor_report_message_handler(payload,topic):

    mqtt_dm_topic=MQTT_msg_topic(topic)
    mqtt_dm_payload=MQTT_msg_payload(payload)
    feed = mqtt_dm_topic.get_0()
    device=json.loads(payload.replace("'",'"'))['device']
    device_id = device['id']
    measures=json.loads(payload.replace("'",'"'))['measures']

    if mqtt_msg.objects.filter(device=device).exists():
        mqtt_msg.objects.filter(device=device).update(measures=measures, report_time=timezone.now())
    else:
        try:

            mqtt_msg(device=device, measures=measures,
                     device_id=device_id, feed=feed).save()
        except:
            pass


def get_topics_list():
    topics_list= list(zip(MQTT_topic.objects.filter(active=True).values_list('topic',flat=True),MQTT_topic.objects.filter(active=True).values_list('qos',flat=True)))
    return topics_list

def mqtt_publish(mqtt_client):
    topic_list = MQTT_tx.objects.all().values_list('topic', flat=True)
    payload_list = MQTT_tx.objects.all().values_list('payload', flat=True)
    for topic, payload in zip(topic_list, payload_list):
        mqtt_client.publish(topic, payload)
    MQTT_tx.objects.all.delete()

def on_connect(mqtt_client, userdata, flags, rc):

    if rc == 0:
        print('Connected successfully')
        mqtt_client.subscribe(get_topics_list())





    else:
        print('Bad connection. Code:', rc)
def on_message(mqtt_client, userdata, msg):
    topic=msg.topic
    payload = str(msg.payload.decode("utf-8", "ignore"))
    print(f'Received message on topic: {msg.topic} with payload: {msg.payload}')
    if 'shellies' in topic:
        sensor_message_handler(payload,topic)
    if 'router/' in topic:
        router_message_handler(payload,topic)
    router_topic = MQTT_feed.objects.filter(name='router').values_list('topic__topic', flat=True)[0].strip('/#')
    if router_topic in topic:
        router_report_message_handler(payload, topic)
    sensor_topic = MQTT_feed.objects.filter(name='shellies').values_list('topic__topic', flat=True)[0].strip('/#')
    if sensor_topic in topic:
        sensor_report_message_handler(payload, topic)
    else:
        general_message_handler(payload,topic)

def on_publish(client,userdata,result):
    #create function for callback
    print("data published \n")
    print (result)
    print (userdata)
    pass
    return

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


@receiver(post_save, sender=MQTT_tx)
def MQTT_tx_post_save(sender, instance, created, **kwargs):
    if created:
        client.publish(instance.topic,instance.payload)
        instance.delete()
