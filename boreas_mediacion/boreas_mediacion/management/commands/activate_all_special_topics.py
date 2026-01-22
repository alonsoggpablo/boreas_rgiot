from django.core.management.base import BaseCommand
from boreas_mediacion.models import MQTT_topic, MQTT_device_family

class Command(BaseCommand):
    help = 'Activate all $SYS, shellies, and shellies2 topics in MQTT_topic table.'

    def handle(self, *args, **options):
        families = ['$SYS', 'shellies', 'shellies2']
        total = 0
        for fam in families:
            fam_obj = MQTT_device_family.objects.filter(name=fam).first()
            if fam_obj:
                updated = MQTT_topic.objects.filter(family=fam_obj, active=False).update(active=True)
                self.stdout.write(f"Activated {updated} topics for family '{fam}'")
                total += updated
            else:
                self.stdout.write(self.style.ERROR(f"Family '{fam}' not found."))
        self.stdout.write(self.style.SUCCESS(f"Total topics activated: {total}"))
