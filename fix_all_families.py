import os
import sys
import django

# Ensure /app/boreas_mediacion is in sys.path for Docker
sys.path.insert(0, '/app/boreas_mediacion')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'boreas_mediacion.settings')
django.setup()

from boreas_mediacion.models import mqtt_msg, MQTT_device_family

families = MQTT_device_family.objects.all()
updated_total = 0
for family in families:
    count = mqtt_msg.objects.filter(feed=family.name, device_family__isnull=True).update(device_family=family)
    print(f"Updated {count} messages for family '{family.name}'")
    updated_total += count
print(f"Total updated messages: {updated_total}")
