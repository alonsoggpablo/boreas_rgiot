#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'boreas_mediacion.settings')
django.setup()

from boreas_mediacion.models import mqtt_msg, MQTT_device_family

# Fix aemet
aemet_fam = MQTT_device_family.objects.get(name='aemet')
aemet_count = mqtt_msg.objects.filter(feed='aemet').update(device_family=aemet_fam)
print(f'Updated {aemet_count} aemet messages')

# Fix router
router_fam = MQTT_device_family.objects.get(name='router')
router_count = mqtt_msg.objects.filter(feed='router').update(device_family=router_fam)
print(f'Updated {router_count} router messages')

# Verify totals
aemet_msgs = mqtt_msg.objects.filter(feed='aemet').count()
router_msgs = mqtt_msg.objects.filter(feed='router').count()
print(f'Total aemet messages: {aemet_msgs}')
print(f'Total router messages: {router_msgs}')
