import csv
import json
from django.core.management.base import BaseCommand
from boreas_mediacion.models import AemetStation

CSV_PATH = '/home/pablo/boreas_rgiot/mqtt_messages_20251229_200620_with_topics.csv'

class Command(BaseCommand):
    help = 'Import AEMET stations from CSV file'

    def handle(self, *args, **options):
        stations = {}
        with open(CSV_PATH, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row['Topic'].startswith('aemet/'):
                    topic_parts = row['Topic'].split('/')
                    province = topic_parts[1] if len(topic_parts) > 2 else None
                    try:
                        payload = json.loads(row['Payload'])
                    except Exception:
                        continue
                    station_id = payload.get('idema') or (topic_parts[2] if len(topic_parts) > 2 else None)
                    name = payload.get('ubi')
                    if not province or province.lower() == 'undefined':
                        province = None
                    if station_id and station_id not in stations:
                        stations[station_id] = {
                            'station_id': station_id,
                            'name': name,
                            'province': province,
                        }
        for s in stations.values():
            obj, created = AemetStation.objects.update_or_create(
                station_id=s['station_id'],
                defaults={
                    'name': s['name'],
                    'province': s['province'],
                    'active': True,
                }
            )
            self.stdout.write(self.style.SUCCESS(f"{'Created' if created else 'Updated'}: {obj}"))