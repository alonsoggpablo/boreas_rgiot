import csv
from django.core.management.base import BaseCommand
from boreas_mediacion.models import MQTT_feed, MQTT_topic, MQTT_device_family, MQTT_broker


class Command(BaseCommand):
    help = 'Load topics and feeds from CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to CSV file')

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        
        # Obtener o crear broker por defecto
        broker, _ = MQTT_broker.objects.get_or_create(
            name='rgiot',
            defaults={
                'server': 'mqtt.solutions-iot.es',
                'port': 8883,
                'user': 'boreas',
                'password': 'RGIoT',
                'keepalive': 60
            }
        )
        
        topics_created = 0
        feeds_created = 0
        families_created = 0
        topics_dict = {}
        
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                topic_str = row['Topic'].strip()
                
                # Parsear topic: topic_1/topic_2/topic_3/...
                parts = topic_str.split('/')
                
                if len(parts) < 2:
                    continue  # Skip topics demasiado cortos
                
                # topic_1 es la device_family (ej: 'aemet', 'IAQ_Measures')
                family_name = parts[0]
                
                # Crear o recuperar MQTT_device_family
                family, created = MQTT_device_family.objects.get_or_create(
                    name=family_name
                )
                if created:
                    families_created += 1
                    self.stdout.write(self.style.SUCCESS(f'Created family: {family_name}'))
                
                # Crear MQTT_topic si no existe
                if topic_str not in topics_dict:
                    topic, created = MQTT_topic.objects.get_or_create(
                        topic=topic_str,
                        defaults={
                            'family': family,
                            'broker': broker,
                            'qos': int(row.get('QoS', 0))
                        }
                    )
                    topics_dict[topic_str] = topic
                    if created:
                        topics_created += 1
                        if topics_created % 100 == 0:
                            self.stdout.write(f'Created {topics_created} topics...')
                else:
                    topic = topics_dict[topic_str]
                
                # Crear MQTT_feed (cada combinación única de topic)
                # Para feeds, usamos topic_2 como device_id si existe
                device_id = parts[1] if len(parts) > 1 else 'default'
                station_id = parts[2] if len(parts) > 2 else None
                
                feed_name = f"{family_name}/{device_id}"
                if station_id:
                    feed_name += f"/{station_id}"
                
                feed, created = MQTT_feed.objects.get_or_create(
                    name=feed_name,
                    topic=topic,
                    defaults={
                        'description': f'Feed for {feed_name}'
                    }
                )
                if created:
                    feeds_created += 1
                    if feeds_created % 100 == 0:
                        self.stdout.write(f'Created {feeds_created} feeds...')
        
        self.stdout.write(self.style.SUCCESS(
            f'\nCompleted!\n'
            f'Families created: {families_created}\n'
            f'Topics created: {topics_created}\n'
            f'Feeds created: {feeds_created}'
        ))
