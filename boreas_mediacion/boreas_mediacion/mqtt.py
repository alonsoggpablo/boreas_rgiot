"""
Legacy MQTT management commands and signal handlers only.
All persistent MQTT ingestion is handled by mqtt_service.py in the mqtt container.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import mqtt_msg, MQTT_tx, sensor_command, router_get

# All legacy/compatibility code only. No classes or logic needed for persistent MQTT.



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
from django.db import connection

def update_device_field(device, field, field_value):
    field_dict = {field: field_value}
    field_dict_str = str(field_dict).replace("'", '"')
    device_str = str(device).replace("'", '"')
    query = f"""update boreas_mediacion_mqtt_msg set report_time=now(),measures=measures ||'{field_dict_str}' where device= '{device_str}' """.replace("\\", "")
    with connection.cursor() as cursor:
        cursor.execute(query)
    # Django autocommits by default
    return

def find_pattern(pattern, string):
    match = re.search(pattern, string)
    return match.group() if match else None

def sensor_message_handler(payload,topic):
    try:
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


        from boreas_mediacion.models import MQTT_device_family
        family = MQTT_device_family.objects.filter(name=feed).first()
        try:
            mqtt_msg(device=mqtt_dm_topic.topic, measures=mqtt_dm_payload.measure,device_id=id,feed=feed, device_family=family).save()
        except:
            mqtt_msg.objects.filter(device=mqtt_dm_topic.topic).update(device=mqtt_dm_topic.topic,
                                                                       measures=mqtt_dm_payload.measure,
                                                                       report_time=timezone.now(),device_id=id,feed=feed, device_family=family)

        if parameter=='total_returned':
            try:
                params_qs = mqtt_msg.objects.filter(device_id=id).values_list('measures', flat=True)
                params = params_qs[0] if params_qs else None
                payload_dict = str({'device': {'id': id, 'circuit': circuit, 'type': type, 'relay': relay}, 'measures': params})
                topic_feed_qs = MQTT_feed.objects.filter(name=feed).values_list('topic__topic', flat=True)
                topic_feed = topic_feed_qs[0] if topic_feed_qs else None
                if topic_feed:
                    MQTT_tx(topic=topic_feed.strip('/#'), payload=payload_dict).save()
            except Exception as e:
                logger.warning(f"Could not process total_returned - {str(e)}")
    except Exception as e:
        logger.warning(f"Error in sensor_message_handler - {str(e)}")

def general_message_handler(payload,topic):
    try:
        mqtt_dm_topic = MQTT_device_measure_topic(topic)
        mqtt_dm_payload = MQTT_device_measure_payload(payload)
        feed= mqtt_dm_topic.get_feed()
        try:
            device_id=json.loads(payload)['device']['id']
        except:
            try: device_id=json.loads(payload)['id']
            except:
                try:device_id=mqtt_dm_topic.get_id()
                except:device_id='no_device_id'

        from boreas_mediacion.models import MQTT_device_family
        # Try to assign device_family based on feed or topic
        family = MQTT_device_family.objects.filter(name=feed).first()
        try:
            mqtt_msg(device=mqtt_dm_topic.topic+'_'+device_id, measures=mqtt_dm_payload.measure,feed=feed,device_id=device_id, device_family=family).save()
        except:
            mqtt_msg.objects.filter(device=mqtt_dm_topic.topic+'_'+device_id).update(device=mqtt_dm_topic.topic+'_'+device_id, measures=mqtt_dm_payload.measure, report_time=timezone.now(),feed=feed,device_id=device_id, device_family=family)
    except Exception as e:
        # Silently ignore errors in general_message_handler
        pass


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
    from boreas_mediacion.models import MQTT_device_family
    router_family = MQTT_device_family.objects.filter(name='router').first()
    if mqtt_msg.objects.filter(device_id=device_id).exists():
        update_device_field(device, parameter, value)
    else:
        try:
            mqtt_msg(device=device, measures=measure,
                     device_id=device_id, feed=feed, device_family=router_family).save()
        except:
            pass

    if parameter=='name':
        params_qs = mqtt_msg.objects.filter(device_id=device_id).values_list('measures', flat=True)
        params = params_qs[0] if params_qs else None
        payload_dict = str({'device': {'id': device_id, 'model': value}, 'params': params})
        topics_qs = MQTT_feed.objects.filter(name=feed).values_list('topic__topic', flat=True)
        topic = topics_qs[0].strip('/#') if topics_qs else None
        MQTT_tx(topic=topic, payload=payload_dict).save()

def router_report_message_handler(payload,topic):

    mqtt_dm_topic=MQTT_msg_topic(topic)
    mqtt_dm_payload=MQTT_msg_payload(payload)
    feed = mqtt_dm_topic.get_0()
    device=json.loads(payload.replace("'",'"'))['device']
    device_id = device['id']
    measures=json.loads(payload.replace("'",'"'))['params']
    from boreas_mediacion.models import MQTT_device_family
    router_family = MQTT_device_family.objects.filter(name='router').first()
    if mqtt_msg.objects.filter(device=device).exists():
        mqtt_msg.objects.filter(device=device).update(measures=measures, report_time=timezone.now(), device_family=router_family)
    else:
        try:
            mqtt_msg(device=device, measures=measures,
                     device_id=device_id, feed=feed, device_family=router_family).save()
        except:
            pass
def sensor_report_message_handler(payload,topic):

    mqtt_dm_topic=MQTT_msg_topic(topic)
    mqtt_dm_payload=MQTT_msg_payload(payload)
    feed = mqtt_dm_topic.get_0()
    try:
        device=json.loads(payload.replace("'",'"'))['device']
        device_id = device['id']
    except:
        device='no_device_id'
        device_id='no_device_id'

    try:
        measures=json.loads(payload.replace("'",'"'))['measures']
    except:measures='no_measures'

    from boreas_mediacion.models import MQTT_device_family
    family = MQTT_device_family.objects.filter(name=feed).first()
    if mqtt_msg.objects.filter(device=device).exists():
        mqtt_msg.objects.filter(device=device).update(measures=measures, report_time=timezone.now(), device_family=family)
    else:
        try:
            mqtt_msg(device=device, measures=measures,
                     device_id=device_id, feed=feed, device_family=family).save()
        except:
            pass

def reported_measure_handler(payload, topic):
    """Handler for reported_measure messages (supports multiple formats)"""
    try:
        mqtt_dm_topic = MQTT_msg_topic(topic)
        feed = mqtt_dm_topic.get_0()
        
        # Parse JSON payload
        payload_data = json.loads(payload.replace("'", '"'))
        
        # Initialize variables
        device_info = {}
        measures_dict = {}
        device_id = 'unknown'
        
        # Check if it's AEMET format (flat JSON with idema field)
        if 'idema' in payload_data:
            # AEMET format: flat JSON with weather station data
            device_id = payload_data.get('idema', 'unknown')
            device_info = {
                'idema': device_id,
                'ubi': payload_data.get('ubi', ''),
                'lon': payload_data.get('lon', 0),
                'lat': payload_data.get('lat', 0),
                'alt': payload_data.get('alt', 0)
            }
            # All other fields are measures
            exclude_fields = {'idema', 'ubi', 'lon', 'lat', 'alt', 'fint'}
            for name, value in payload_data.items():
                if name not in exclude_fields:
                    # Determine unit based on field name
                    unit = ''
                    if name in ['prec', 'pacutp']: unit = 'mm'
                    elif name in ['vmax', 'vv']: unit = 'm/s'
                    elif name in ['dv', 'dmax']: unit = 'degrees'
                    elif name in ['pres', 'pres_nmar']: unit = 'hPa'
                    elif name in ['hr']: unit = '%'
                    elif name in ['ta', 'tamin', 'tamax', 'tpr', 'ts', 'tss5cm', 'tss20cm']: unit = '°C'
                    elif name in ['vis']: unit = 'km'
                    elif name in ['inso']: unit = 'min'
                    measures_dict[name] = {'value': value, 'unit': unit}
            # Also save to mqtt_msg with correct device_family
            from boreas_mediacion.models import MQTT_device_family
            family = MQTT_device_family.objects.filter(name='aemet').first()
            try:
                mqtt_msg(device=device_info, device_id=device_id, feed='aemet', measures=measures_dict, device_family=family).save()
            except Exception as e:
                try:
                    mqtt_msg.objects.filter(device_id=device_id, feed='aemet').update(device=device_info, measures=measures_dict, report_time=timezone.now(), device_family=family)
                except Exception as update_error:
                    logger.warning(f"Could not save/update mqtt_msg for aemet - {str(update_error)}")
        
        # Check if it has device_info or device structure
        elif 'device_info' in payload_data or 'device' in payload_data:
            # Extract device info - support both 'device_info' and 'device' keys
            device_info = payload_data.get('device_info', None)
            if device_info is None:
                device_info = payload_data.get('device', {})
            
            # Extract measures - support both array and object formats
            measures_raw = payload_data.get('measures', None)
            
            # Get device_id - from 'uuid' (device_info) or 'id' (device)
            device_id = device_info.get('uuid', device_info.get('id', 'unknown'))
            
            # Convert measures to standardized dict format
            if isinstance(measures_raw, list):
                # Array format: [{"n": "co2", "u": "ppm", "v": 590.984}, ...]
                for measure in measures_raw:
                    name = measure.get('n', '')
                    value = measure.get('v', 0)
                    unit = measure.get('u', '')
                    if name:
                        measures_dict[name] = {'value': value, 'unit': unit}
            elif isinstance(measures_raw, dict):
                # Object format: {"energy": "110", "power": "109.59", ...}
                for name, value in measures_raw.items():
                    measures_dict[name] = {'value': value, 'unit': ''}
        else:
            # Unknown format, skip
            return
        
        # Save to reported_measure model
        try:
            reported_measure(
                device=device_info,
                device_id=device_id,
                measures=measures_dict,
                feed=feed
            ).save()
        except Exception as e:
            # Try to update if already exists
            try:
                reported_measure.objects.filter(device_id=device_id).update(
                    device=device_info,
                    measures=measures_dict,
                    report_time=timezone.now(),
                    feed=feed
                )
            except Exception as update_error:
                logger.warning(f"Could not save/update reported measure - {str(update_error)}")
    
    except Exception as e:
        logger.warning(f"Error in reported_measure_handler - {str(e)}")


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
        logger.info('MQTT connected successfully')
        mqtt_client.subscribe(get_topics_list())
    else:
        logger.error('MQTT bad connection. Code: %s', rc)

def on_disconnect(mqtt_client, userdata, rc):
    if rc != 0:
        logger.warning(f'Unexpected disconnection. Code: {rc}')
    else:
        logger.info('MQTT disconnected')
    # Attempt to reconnect
    try:
        mqtt_client.reconnect()
        logger.info('MQTT reconnect initiated')
    except Exception as e:
        logger.warning(f'Could not reconnect to MQTT broker - {str(e)}')

def on_message(mqtt_client, userdata, msg):
    topic=msg.topic
    payload = str(msg.payload.decode("utf-8", "ignore"))
    logger.debug(f'Received message on topic: {msg.topic} with payload: {msg.payload}')
    
    # First, check if payload has reported_measure structure
    # Supports: device_info + measures, device + measures, or AEMET format (idema)
    try:
        payload_data = json.loads(payload.replace("'", '"'))
        # Check for AEMET format (has idema field)
        if 'idema' in payload_data:
            reported_measure_handler(payload, topic)
            return  # Exit after handling AEMET message
        # Check for device_info/device with measures
        elif ('device_info' in payload_data or 'device' in payload_data) and 'measures' in payload_data:
            reported_measure_handler(payload, topic)
            return  # Exit after handling reported_measure message
    except Exception as e:
        pass  # Not a JSON or not a reported_measure format, continue to other handlers
    
    # Handle Shellies devices
    if 'shellies' in topic:
        sensor_message_handler(payload,topic)
        # Try to handle sensor report if feed exists
        try:
            sensor_topic = MQTT_feed.objects.filter(name='shellies').values_list('topic__topic', flat=True).first()
            if sensor_topic and sensor_topic.strip('/#') in topic:
                sensor_report_message_handler(payload, topic)
        except Exception as e:
            logger.warning(f"Could not process sensor report - {str(e)}")

    # Handle SYS devices
    elif 'SYS' in topic or '$SYS' in topic or topic.startswith('SYS') or topic.startswith('$SYS'):
        try:
            from boreas_mediacion.models import MQTT_device_family
            sys_family = MQTT_device_family.objects.filter(name='SYS').first()
            mqtt_dm_topic = MQTT_msg_topic(topic)
            mqtt_dm_payload = MQTT_msg_payload(payload)
            device_id = mqtt_dm_topic.get_1()
            parameter = mqtt_dm_topic.get_2()
            value = mqtt_dm_payload.get_0()
            feed = mqtt_dm_topic.get_0()
            measure = {parameter: value}
            mqtt_msg(device=device_id, measures=measure, device_id=device_id, feed=feed, device_family=sys_family).save()
        except Exception as e:
            logger.warning(f"Could not process SYS message - {str(e)}")

    # Handle gadget devices
    elif 'gadget' in topic or topic.startswith('gadget'):
        try:
            from boreas_mediacion.models import MQTT_device_family
            gadget_family = MQTT_device_family.objects.filter(name='gadget').first()
            # Try to parse new gadget message format
            try:
                payload_data = json.loads(payload.replace("'", '"'))
                if 'gadget' in payload_data and 'data' in payload_data:
                    device_info = payload_data['gadget']
                    device_id = device_info.get('uuid', 'unknown')
                    measures = payload_data['data']
                    feed = 'gadget'
                    mqtt_msg(device=device_info, measures=measures, device_id=device_id, feed=feed, device_family=gadget_family).save()
                    return
            except Exception as e:
                logger.warning(f"Could not parse new gadget format: {str(e)}")
            # Fallback to old logic
            mqtt_dm_topic = MQTT_msg_topic(topic)
            mqtt_dm_payload = MQTT_msg_payload(payload)
            device_id = mqtt_dm_topic.get_1()
            parameter = mqtt_dm_topic.get_2()
            value = mqtt_dm_payload.get_0()
            feed = mqtt_dm_topic.get_0()
            measure = {parameter: value}
            mqtt_msg(device=device_id, measures=measure, device_id=device_id, feed=feed, device_family=gadget_family).save()
        except Exception as e:
            logger.warning(f"Could not process gadget message - {str(e)}")

    # Handle RPC devices
    elif 'rpc/' in topic or '/rpc/' in topic or topic.startswith('rpc'):
        try:
            from boreas_mediacion.models import MQTT_device_family
            rpc_family = MQTT_device_family.objects.filter(name='rpc').first()
            mqtt_dm_topic = MQTT_msg_topic(topic)
            mqtt_dm_payload = MQTT_msg_payload(payload)
            device_id = mqtt_dm_topic.get_1()
            parameter = mqtt_dm_topic.get_2()
            value = mqtt_dm_payload.get_0()
            feed = mqtt_dm_topic.get_0()
            measure = {parameter: value}
            # Save with device_family=rpc_family
            mqtt_msg(device=device_id, measures=measure, device_id=device_id, feed=feed, device_family=rpc_family).save()
        except Exception as e:
            logger.warning(f"Could not process RPC message - {str(e)}")

    # Handle Router devices
    elif 'router/' in topic:
        router_message_handler(payload,topic)
        # Try to handle router report if feed exists
        try:
            router_topic = MQTT_feed.objects.filter(name='router').values_list('topic__topic', flat=True).first()
            if router_topic and router_topic.strip('/#') in topic:
                router_report_message_handler(payload, topic)
        except Exception as e:
            logger.warning(f"Could not process router report - {str(e)}")

    # Handle other messages
    else:
        general_message_handler(payload,topic)

def on_publish(client,userdata,result):
    #create function for callback
    logger.debug("data published")
    print (result)
    print (userdata)
    pass
    return


def MQTT_tx_post_save(sender, instance, created, **kwargs):
    # Legacy: implement direct publish if needed for management commands
    pass


def send_command(sender, instance,created, **kwargs):
    # Legacy: implement direct publish if needed for management commands
    pass

def get_router_parameter(sender, instance,created, **kwargs):
    # Legacy: implement direct publish if needed for management commands
    pass