from django.core.management.base import BaseCommand
from boreas_mediacion.models import MQTT_device_family, mqtt_msg

class Command(BaseCommand):
    help = 'Show last message time and count for each MQTT device family.'

    def handle(self, *args, **options):
        families = MQTT_device_family.objects.all()
        self.stdout.write('Family           | Last Message         | Count')
        self.stdout.write('-'*50)
        for fam in families:
            last = mqtt_msg.objects.filter(device_family=fam).order_by('-report_time').first()
            count = mqtt_msg.objects.filter(device_family=fam).count()
            last_time = getattr(last, "report_time", None)
            self.stdout.write(f'{fam.name:15} | {last_time} | {count}')
