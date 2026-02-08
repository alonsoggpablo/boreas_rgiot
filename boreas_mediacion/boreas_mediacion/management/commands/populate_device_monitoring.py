from django.core.management.base import BaseCommand
from boreas_mediacion.models import DeviceMonitoring, ExternalDeviceMapping


class Command(BaseCommand):
    help = 'Populate DeviceMonitoring table with all external devices from ExternalDeviceMapping'

    def handle(self, *args, **options):
        created_count = 0
        # Populate from local ExternalDeviceMapping table
        for device in ExternalDeviceMapping.objects.all():
            obj, created = DeviceMonitoring.objects.get_or_create(
                uuid=str(device.external_device_id),
                defaults={
                    'monitored': True
                }
            )
            if obj.external_device_id is None:
                obj.external_device = device
                obj.save(update_fields=['external_device'])
            if created:
                created_count += 1

        total = DeviceMonitoring.objects.count()
        self.stdout.write(self.style.SUCCESS(f'Created {created_count} new records. Total: {total}'))
