from django.core.management.base import BaseCommand
from boreas_mediacion.models import MQTT_topic, MQTT_device_family

class Command(BaseCommand):
    help = 'Activate only one topic per family (the first found), deactivate the rest.'

    def handle(self, *args, **options):
        families = MQTT_device_family.objects.all()
        for family in families:
            topics = MQTT_topic.objects.filter(family=family)
            if topics.exists():
                topics.update(active=False)
                first_topic = topics.first()
                first_topic.active = True
                first_topic.save()
                self.stdout.write(self.style.SUCCESS(f"Activated topic {first_topic.topic} for family {family.name}"))
            else:
                self.stdout.write(self.style.WARNING(f"No topics found for family {family.name}"))
        self.stdout.write(self.style.SUCCESS("Done."))
