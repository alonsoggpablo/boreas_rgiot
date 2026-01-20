import time
from django.core.management.base import BaseCommand
from boreas_mediacion.models import MQTT_broker, MQTT_topic
import paho.mqtt.client as mqtt

class Command(BaseCommand):
    help = 'Test MQTT subscription for a topic and print received messages.'

    def add_arguments(self, parser):
        parser.add_argument('--topic', type=str, default='rgiot/#', help='MQTT topic to subscribe to')
        parser.add_argument('--timeout', type=int, default=15, help='Seconds to listen for messages')

    def handle(self, *args, **options):
        topic = options['topic']
        timeout = options['timeout']
        broker = MQTT_broker.objects.filter(name='rgiot').first()
        if not broker:
            self.stdout.write(self.style.ERROR("No 'rgiot' broker found in DB."))
            return
        client = mqtt.Client()
        client.username_pw_set(broker.user, broker.password)
        client.tls_set()
        messages = []
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                self.stdout.write(f"Connected to MQTT broker {broker.server}:{broker.port}")
                client.subscribe(topic)
            else:
                self.stdout.write(self.style.ERROR(f"Failed to connect, code {rc}"))
        def on_message(client, userdata, msg):
            self.stdout.write(f"Message on {msg.topic}: {msg.payload.decode('utf-8', errors='ignore')}")
            messages.append((msg.topic, msg.payload))
        client.on_connect = on_connect
        client.on_message = on_message
        client.connect(broker.server, broker.port, broker.keepalive)
        client.loop_start()
        self.stdout.write(f"Listening for messages on '{topic}' for {timeout} seconds...")
        time.sleep(timeout)
        client.loop_stop()
        client.disconnect()
        self.stdout.write(f"Received {len(messages)} messages.")