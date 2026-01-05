#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'boreas_mediacion.settings')
django.setup()

from boreas_mediacion.models import MQTT_broker, MQTT_device_family, MQTT_topic, MQTT_feed

# 1. Crear familia AEMET
family, created = MQTT_device_family.objects.get_or_create(name='AEMET')
print(f"Family AEMET: {'Created' if created else 'Already exists'}")

# 2. Obtener broker (ya debe existir desde antes)
try:
    broker = MQTT_broker.objects.get(name='rgiot')
    print(f"Broker rgiot found")
except:
    print("ERROR: Broker 'rgiot' not found. Create it first in Admin.")
    exit(1)

# 3. Crear topic AEMET
topic, created = MQTT_topic.objects.get_or_create(
    broker=broker,
    family=family,
    topic='aemet/+/+',
    defaults={
        'qos': 0,
        'description': 'AEMET Weather Stations',
        'active': True,
        'ro_rw': 'ro'
    }
)
print(f"Topic AEMET: {'Created' if created else 'Already exists'}")

# 4. Crear feeds
feeds_data = [
    ('temperature', 'Temperatura actual (°C)'),
    ('temperature_max', 'Temperatura máxima (°C)'),
    ('temperature_min', 'Temperatura mínima (°C)'),
    ('humidity', 'Humedad relativa (%)'),
    ('pressure', 'Presión barométrica (hPa)'),
    ('wind_speed', 'Velocidad del viento (m/s)'),
    ('wind_direction', 'Dirección del viento (grados)'),
    ('precipitation', 'Precipitación (mm)'),
    ('visibility', 'Visibilidad (km)'),
]

for feed_name, description in feeds_data:
    feed, created = MQTT_feed.objects.get_or_create(
        name=feed_name,
        topic=topic,
        defaults={'description': description}
    )
    status = 'Created' if created else 'Already exists'
    print(f"Feed {feed_name}: {status}")

print("\n✅ AEMET configuration complete!")
