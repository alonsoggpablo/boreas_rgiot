#!/usr/bin/env python
"""
Standalone MQTT Service
Runs in a separate Docker container and handles all MQTT communication
"""
import json
import re
import ssl
import logging
import os
import sys
import time
import paho.mqtt.client as mqtt
import django

# Configure Django BEFORE any imports from boreas_mediacion
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "boreas_mediacion.settings")
sys.path.insert(0, '/app/boreas_mediacion')

django.setup()

from datetime import datetime, timedelta
from django.utils import timezone
from boreas_mediacion.models import mqtt_msg, reported_measure, MQTT_broker, MQTT_topic, MQTT_tx, MQTT_feed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - MQTT Service - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import message handlers - we'll define these locally instead of importing from mqtt.py
# to avoid circular imports and double Django setup

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

def general_message_handler(payload, topic):
    """Handle general MQTT messages from devices"""
    try:
        topic_obj = MQTT_device_measure_topic(topic)
        device_id = topic_obj.get_id()
        feed = topic_obj.get_feed()

        # Parse JSON payload if possible
        try:
            measures = json.loads(payload)
        except:
            measures = {"value": payload}

        # Buscar coincidencia por prefijo en los topics activos
        topic_record = None
        for t in MQTT_topic.objects.filter(active=True):
            if topic.startswith(t.topic):
                topic_record = t
                break
        family = topic_record.family if topic_record else None

        # Use update_or_create to handle uniqueness on device field
        device_data = {"device_id": device_id, "feed": feed}
        mqtt_msg.objects.update_or_create(
            device=device_data,
            defaults={
                "device_id": device_id,
                "measures": measures,
                "feed": feed,
                "device_family": family
            }
        )
        logger.debug(f"Message saved: {device_id} from {topic} (family: {family})")
    except Exception as e:
        logger.error(f"Error in general_message_handler: {str(e)}")

def router_report_message_handler(payload, topic):
    """Handle router report messages"""
    try:
        try:
            measures = json.loads(payload)
        except:
            measures = {"value": payload}

        # Obtener device_id y familia router
        from boreas_mediacion.models import MQTT_device_family
        # Extraer device_id del topic router/<device_id>
        try:
            device_id = topic.split('/')[1]
        except:
            device_id = 'unknown'
        family = MQTT_device_family.objects.filter(name='router').first()

        mqtt_msg.objects.update_or_create(
            device={"device_id": device_id, "feed": "router"},
            defaults={
                "device_id": device_id,
                "measures": measures,
                "feed": "router",
                "device_family": family
            }
        )
        logger.debug(f"Router message saved: {device_id} from {topic} (family: {family})")
    except Exception as e:
        logger.error(f"Error in router_report_message_handler: {str(e)}")

# MQTT Configuration
mqtt_client = None
mqtt_running = False

def on_connect(client, userdata, flags, rc):
    """MQTT connection callback"""
    if rc == 0:
        logger.info("MQTT connected successfully")
        # Subscribe to all active topics
        try:
            topics_list = MQTT_topic.objects.filter(active=True).values_list('topic', flat=True)
            logger.info(f"Subscribing to {len(topics_list)} topics")
            
            for topic in topics_list:
                client.subscribe(topic)
            logger.info("All topics subscribed successfully")
        except Exception as e:
            logger.error(f"Error subscribing to topics: {str(e)}")
    else:
        logger.error(f"Failed to connect, return code {rc}")

def on_disconnect(client, userdata, rc):
    """MQTT disconnection callback"""
    if rc != 0:
        logger.warning(f'Unexpected disconnection. Code: {rc}')
    else:
        logger.info('MQTT disconnected cleanly')
    
    # Set disconnect flag for periodic retry
    global mqtt_running, mqtt_disconnected
    mqtt_disconnected = True

def on_message(client, userdata, msg):
    """MQTT message callback"""
    try:
        topic = msg.topic
        payload = msg.payload.decode('utf-8', errors='ignore')
        logger.debug(f"Message received on {topic}: {payload}")
        
        # Parse the message based on topic structure
        topic_obj = MQTT_device_measure_topic(topic)
        device_type = topic_obj.get_type()
        device_id = topic_obj.get_id()
        relay = topic_obj.get_relay()
        circuit = topic_obj.get_circuit()
        parameter = topic_obj.get_parameter()
        feed = topic_obj.get_feed()
        
        # Route to appropriate handler
        if device_type in ['shelly1pm', 'shellyem3', 'shellypro4pm']:
            general_message_handler(payload, topic)
        elif feed == 'router':
            router_report_message_handler(payload, topic)
        elif feed == 'shellies2' or 'shellies2' in topic:
            # Explicitly assign shellies2 family
            from boreas_mediacion.models import MQTT_device_family
            family = MQTT_device_family.objects.filter(name='shellies2').first()
            topic_obj = MQTT_device_measure_topic(topic)
            device_id = topic_obj.get_id()
            feed_val = topic_obj.get_feed()
            try:
                measures = json.loads(payload)
            except:
                measures = {"value": payload}
            mqtt_msg.objects.update_or_create(
                device={"device_id": device_id, "feed": feed_val},
                defaults={
                    "device_id": device_id,
                    "measures": measures,
                    "feed": feed_val,
                    "device_family": family
                }
            )
            logger.debug(f"shellies2 message saved: {device_id} from {topic}")
        else:
            general_message_handler(payload, topic)
            
    except Exception as e:
        logger.error(f"Error processing message on {topic}: {str(e)}")

def on_publish(client, userdata, result):
    """MQTT publish callback"""
    logger.debug(f"Message published, result: {result}")

def initialize_mqtt():
    """Initialize MQTT client"""
    global mqtt_client, mqtt_running
    
    try:
        # Get MQTT broker configuration from database
        mqtt_broker = MQTT_broker.objects.filter(name='rgiot').first()
        if not mqtt_broker:
            logger.error("MQTT broker 'rgiot' not found in database")
            return False
        
        mqtt_server = mqtt_broker.server
        mqtt_port = mqtt_broker.port
        mqtt_keepalive = mqtt_broker.keepalive
        mqtt_user = mqtt_broker.user
        mqtt_password = mqtt_broker.password
        
        logger.info(f"Connecting to {mqtt_server}:{mqtt_port} as {mqtt_user}")
        
        # Create and configure MQTT client
        mqtt_client = mqtt.Client(client_id=f"mqtt_service_{os.getpid()}")
        mqtt_client.on_connect = on_connect
        mqtt_client.on_disconnect = on_disconnect
        mqtt_client.on_message = on_message
        mqtt_client.on_publish = on_publish
        
        # Set credentials
        mqtt_client.username_pw_set(mqtt_user, mqtt_password)
        
        # Enable TLS for port 8883
        mqtt_client.tls_set(
            certfile=None,
            keyfile=None,
            cert_reqs=ssl.CERT_NONE,
            tls_version=ssl.PROTOCOL_TLSv1_2,
            ciphers=None
        )
        
        # Connect to broker
        mqtt_client.connect(
            host=mqtt_server,
            port=mqtt_port,  # Use port from DB (should be 8883)
            keepalive=mqtt_keepalive
        )
        
        # Start network loop
        mqtt_client.loop_start()
        mqtt_running = True
        logger.info("MQTT client initialized and started successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize MQTT client: {str(e)}")
        mqtt_client = None
        mqtt_running = False
        return False

def keep_alive():
    """Keep the service running"""
    global mqtt_running, mqtt_disconnected, mqtt_client
    logger.info("MQTT Service running. Press Ctrl+C to stop.")
    last_retry = time.time()
    try:
        while mqtt_running:
            time.sleep(1)
            # Retry every 10 minutes if disconnected
            if mqtt_disconnected and (time.time() - last_retry) > 600:
                logger.info("Retrying MQTT connection after disconnect...")
                try:
                    mqtt_client.reconnect()
                    mqtt_disconnected = False
                    logger.info("MQTT reconnect successful.")
                except Exception as e:
                    logger.warning(f"MQTT reconnect failed: {str(e)}")
                last_retry = time.time()
    except KeyboardInterrupt:
        logger.info("Shutting down MQTT Service...")
        if mqtt_client:
            mqtt_client.loop_stop()
            mqtt_running = False
        sys.exit(0)

if __name__ == "__main__":
    logger.info("Starting MQTT Service...")
    mqtt_disconnected = False
    # Give database time to start if this container starts before db
    max_retries = 30
    for attempt in range(max_retries):
        if initialize_mqtt():
            keep_alive()
            break
        else:
            logger.warning(f"Connection attempt {attempt + 1}/{max_retries} failed. Retrying in 10 seconds...")
            time.sleep(10)
    logger.error("Failed to start MQTT Service after maximum retries")
    sys.exit(1)
