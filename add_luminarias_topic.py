#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'boreas_mediacion.settings')
sys.path.insert(0, 'c:\\Users\\Usuario\\Documents\\GitHub\\boreas_rgiot\\boreas_mediacion')
django.setup()

from boreas_mediacion.models import MQTT_topic, MQTT_broker, MQTT_device_family

# Get or create broker and family
broker = MQTT_broker.objects.filter(alias='mqtt.rg-iotsolutions.com').first() or MQTT_broker.objects.first()
family = MQTT_device_family.objects.filter(name__icontains='luminarias').first() or MQTT_device_family.objects.first()

if not broker:
    print("ERROR: No MQTT broker found")
    sys.exit(1)
else:
    print(f"Using broker: {broker.alias}")

if not family:
    print("WARNING: No device family found for 'luminarias'")
    print("Available families:")
    for f in MQTT_device_family.objects.all():
        print(f"  - {f.name} (id: {f.id})")
    print("Using first available family...")
    family = MQTT_device_family.objects.first()

if not family:
    print("ERROR: No device families exist in database")
    sys.exit(1)
else:
    print(f"Using family: {family.name}")

# Check if topic already exists
existing = MQTT_topic.objects.filter(topic='RPC/tactica/luminarias/#').first()
if existing:
    print(f"\nTopic already exists: {existing.topic}")
    print(f"  Active: {existing.active}")
    print(f"  RO/RW: {existing.ro_rw}")
    print(f"  QoS: {existing.qos}")
    print(f"  Description: {existing.description}")
else:
    # Create new topic
    topic = MQTT_topic.objects.create(
        broker=broker,
        family=family,
        topic='RPC/tactica/luminarias/#',
        qos=0,
        description='RPC for controlling luminarias (lighting) devices via Tactica',
        active=True,
        ro_rw='rw'  # read-write since we need to send commands
    )
    print(f"\nCreated new topic:")
    print(f"  Topic: {topic.topic}")
    print(f"  Active: {topic.active}")
    print(f"  RO/RW: {topic.ro_rw}")
    print(f"  QoS: {topic.qos}")
    print(f"  Description: {topic.description}")
