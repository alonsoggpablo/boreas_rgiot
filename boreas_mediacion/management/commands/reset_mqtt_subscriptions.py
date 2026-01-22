from django.core.management.base import BaseCommand
from boreas_mediacion.models import MQTT_device_family, MQTT_topic

class Command(BaseCommand):
    help = 'Desactiva todas las suscripciones MQTT y deja solo un topic activo por familia.'

    def handle(self, *args, **options):
        total_deactivated = 0
        total_activated = 0
        # Desactivar todas
        MQTT_topic.objects.filter(active=True).update(active=False)
        self.stdout.write(self.style.WARNING('Todas las suscripciones han sido desactivadas.'))

        for family in MQTT_device_family.objects.all():
            topic = MQTT_topic.objects.filter(family=family).order_by('id').first()
            if topic:
                topic.active = True
                topic.save(update_fields=['active'])
                total_activated += 1
                self.stdout.write(self.style.SUCCESS(f"Activado topic '{topic.topic}' para familia '{family.name}'"))

        self.stdout.write(self.style.SUCCESS(f"Total topics activados: {total_activated}"))