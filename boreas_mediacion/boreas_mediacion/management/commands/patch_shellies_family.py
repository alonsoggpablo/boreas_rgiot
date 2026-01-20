from django.core.management.base import BaseCommand
from boreas_mediacion.models import mqtt_msg, MQTT_device_family

class Command(BaseCommand):
    help = 'Patch old shellies mqtt_msg records to set device_family.'

    def handle(self, *args, **options):
        shellies_family = MQTT_device_family.objects.filter(name='shellies').first()
        if not shellies_family:
            self.stdout.write(self.style.ERROR("No 'shellies' family found."))
            return
        count = 0
        # Patch all mqtt_msg records with feed starting with 'shellies/' and no device_family
        for msg in mqtt_msg.objects.filter(feed__startswith='shellies/').filter(device_family__isnull=True):
            msg.device_family = shellies_family
            msg.save()
            count += 1
        self.stdout.write(f"Patched {count} shellies messages.")
