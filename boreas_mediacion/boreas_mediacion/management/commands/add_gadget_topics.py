from django.core.management.base import BaseCommand
from boreas_mediacion.external_device_models import ExternalDevice
from boreas_mediacion.models import MQTT_topic, MQTT_broker, MQTT_device_family
from django.db import transaction

class Command(BaseCommand):
    help = 'Add gadget/DEVICE_ID topics to MQTT_topic for all ExternalDevice device_ids (no duplicates)'

    def handle(self, *args, **options):
        device_ids = list(ExternalDevice.objects.values_list('device_id', flat=True))
        broker = MQTT_broker.objects.filter(active=True).first()
        if not broker:
            broker = MQTT_broker.objects.create(name='default', server='localhost', port=1883, active=True)
        family = MQTT_device_family.objects.filter(name='unknown').first()
        if not family:
            family = MQTT_device_family.objects.create(name='unknown')
        existing_topics = set(MQTT_topic.objects.values_list('topic', flat=True))
        new_topics = []
        for device_id in device_ids:
            topic = f'gadget/{device_id}'
            if topic not in existing_topics:
                new_topics.append(MQTT_topic(broker=broker, family=family, topic=topic, qos=0, active=True, ro_rw='ro'))
        with transaction.atomic():
            MQTT_topic.objects.bulk_create(new_topics, ignore_conflicts=True)
        self.stdout.write(self.style.SUCCESS(f'Added {len(new_topics)} new gadget topics.'))
