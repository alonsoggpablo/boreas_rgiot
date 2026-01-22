from django.core.management.base import BaseCommand
from boreas_mediacion.models import mqtt_msg

class Command(BaseCommand):
    help = 'Elimina todos los mensajes recibidos (mqtt_msg) de la base de datos.'

    def handle(self, *args, **options):
        count, _ = mqtt_msg.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f"Se han eliminado {count} mensajes MQTT."))
