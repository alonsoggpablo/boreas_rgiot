from django.core.management.base import BaseCommand
from boreas_mediacion.models import reported_measure
from boreas_bot.models import DevicesNANOENVI


class Command(BaseCommand):
    help = 'Populate nanoenvi_uuid, nanoenvi_name, and nanoenvi_client fields in reported_measure'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        self.stdout.write(self.style.SUCCESS('Starting population of nanoenvi fields...'))
        
        # Get all unique device_ids that might be nanoenvi UUIDs
        device_ids = reported_measure.objects.values_list('device_id', flat=True).distinct()
        
        # Build a mapping of UUID to nanoenvi data
        nanoenvi_map = {}
        for device_id in device_ids:
            try:
                nano = DevicesNANOENVI.objects.get(uuid=device_id)
                nanoenvi_map[device_id] = {
                    'uuid': nano.uuid,
                    'name': nano.name,
                    'client': nano.client,
                }
            except DevicesNANOENVI.DoesNotExist:
                pass
        
        self.stdout.write(f'Found {len(nanoenvi_map)} matching device_ids')
        
        # Update reported_measure records
        total_updated = 0
        for device_id, nano_data in nanoenvi_map.items():
            qs = reported_measure.objects.filter(device_id=device_id)
            count = qs.count()
            
            if not dry_run:
                qs.update(
                    nanoenvi_uuid=nano_data['uuid'],
                    nanoenvi_name=nano_data['name'],
                    nanoenvi_client=nano_data['client'],
                )
                self.stdout.write(f"  Updated {count} records for device_id: {device_id}")
            else:
                self.stdout.write(f"  Would update {count} records for device_id: {device_id}")
            
            total_updated += count
        
        if dry_run:
            self.stdout.write(self.style.WARNING(f'DRY RUN: Would have updated {total_updated} records'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Successfully updated {total_updated} records'))
