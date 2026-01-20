from django.core.management.base import BaseCommand
from boreas_mediacion.models import MQTT_topic

class Command(BaseCommand):
    help = 'Activate all shellies topics in MQTT_topic table.'

    def handle(self, *args, **options):
        updated = MQTT_topic.objects.filter(family__name='shellies', active=False).update(active=True)
        self.stdout.write(f"Activated {updated} shellies topics.")
