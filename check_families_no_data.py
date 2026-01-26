from boreas_mediacion.models import MQTT_device_family, mqtt_msg
families = MQTT_device_family.objects.all()
for family in families:
    last_msg = mqtt_msg.objects.filter(device_family=family).order_by('-report_time').first()
    print(family.name, 'NO DATA' if not last_msg else last_msg.device_id)
