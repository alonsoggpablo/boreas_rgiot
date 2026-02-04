from django.core.management.base import BaseCommand
from boreas_mediacion.models import DeviceMonitoring
from boreas_bot.models import DevicesNANOENVI, DevicesCO2, DevicesROUTERS


class Command(BaseCommand):
    help = 'Populate DeviceMonitoring table with all external devices'

    def handle(self, *args, **options):
        created_count = 0

        # NANOENVI
        for d in DevicesNANOENVI.objects.all():
            obj, created = DeviceMonitoring.objects.get_or_create(
                uuid=str(d.uuid),
                source='nanoenvi',
                defaults={'monitored': True}
            )
            if created:
                created_count += 1

        # CO2
        for d in DevicesCO2.objects.all():
            obj, created = DeviceMonitoring.objects.get_or_create(
                uuid=str(d.id),
                source='co2',
                defaults={'monitored': True}
            )
            if created:
                created_count += 1

        # ROUTERS
        for d in DevicesROUTERS.objects.all():
            obj, created = DeviceMonitoring.objects.get_or_create(
                uuid=str(d.id),
                source='routers',
                defaults={'monitored': True}
            )
            if created:
                created_count += 1

        total = DeviceMonitoring.objects.count()
        self.stdout.write(self.style.SUCCESS(f'Created {created_count} new records. Total: {total}'))
