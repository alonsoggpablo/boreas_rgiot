# Patch old mqtt_msg entries for gadget and router families
from boreas_mediacion.models import mqtt_msg, MQTT_device_family
from django.db import transaction

def patch_gadget_router_family():
    fam_gadget = MQTT_device_family.objects.get(name='gadget')
    fam_router = MQTT_device_family.objects.get(name='router')
    # Patch gadget messages
    gadget_msgs = mqtt_msg.objects.filter(feed__icontains='gadget', device_family__isnull=True)
    for msg in gadget_msgs:
        msg.device_family = fam_gadget
        msg.save(update_fields=['device_family'])
    # Patch router messages
    router_msgs = mqtt_msg.objects.filter(feed__icontains='router', device_family__isnull=True)
    for msg in router_msgs:
        msg.device_family = fam_router
        msg.save(update_fields=['device_family'])
    print(f"Patched {gadget_msgs.count()} gadget and {router_msgs.count()} router messages.")

if __name__ == "__main__":
    patch_gadget_router_family()
