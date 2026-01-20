# Patch old mqtt_msg entries for gadget family with new format
from boreas_mediacion.models import mqtt_msg, MQTT_device_family
from django.db import transaction

def patch_gadget_family():
    fam_gadget = MQTT_device_family.objects.get(name='gadget')
    # Find messages with gadget format in device field and no device_family
    gadget_msgs = mqtt_msg.objects.filter(feed='gadget', device_family__isnull=True, device__has_key='uuid')
    for msg in gadget_msgs:
        msg.device_family = fam_gadget
        msg.save(update_fields=['device_family'])
    print(f"Patched {gadget_msgs.count()} gadget messages.")

if __name__ == "__main__":
    patch_gadget_family()
