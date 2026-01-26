import csv
import json
from django.utils import timezone
from boreas_mediacion.models import AemetStation

# Path to the CSV file
CSV_PATH = '/home/pablo/boreas_rgiot/mqtt_messages_20251229_200620_with_topics.csv'

# Set to True to actually save, False to just print
DO_SAVE = True

def parse_aemet_rows():
    stations = {}
    with open(CSV_PATH, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row['Topic'].startswith('aemet/'):
                # Try to get province and station_id from topic
                topic_parts = row['Topic'].split('/')
                province = topic_parts[1] if len(topic_parts) > 2 else None
                # Parse payload JSON
                try:
                    payload = json.loads(row['Payload'])
                except Exception:
                    continue
                station_id = payload.get('idema') or (topic_parts[2] if len(topic_parts) > 2 else None)
                name = payload.get('ubi')
                # Use first non-empty value for province
                if not province or province.lower() == 'undefined':
                    province = None
                # Use a dict to deduplicate by station_id
                if station_id and station_id not in stations:
                    stations[station_id] = {
                        'station_id': station_id,
                        'name': name,
                        'province': province,
                    }
    return list(stations.values())

def import_stations():
    stations = parse_aemet_rows()
    for s in stations:
        obj, created = AemetStation.objects.update_or_create(
            station_id=s['station_id'],
            defaults={
                'name': s['name'],
                'province': s['province'],
                'active': True,
            }
        )
        print(f"{'Created' if created else 'Updated'}: {obj}")

if __name__ == '__main__':
    import_stations()
