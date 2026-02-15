from django.core.management.base import BaseCommand
from boreas_mediacion.models import reported_measure, Gadget

class Command(BaseCommand):
    help = 'Populate name and client fields in reported_measure from Gadget table'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )

    def handle(self, *args, **options):
        """
        Populates the 'name' and 'client' fields of reported_measure records based on matching device IDs from the Gadget table.

        For each unique device_id in reported_measure, this command looks up the corresponding Gadget by device_id.
        If a match is found, it updates all reported_measure records with that device_id, setting:
            - 'name' to the Gadget's alias (or empty string if not set)
            - 'client' to the Gadget's cliente (or empty string if not set)

        The process can be run in dry-run mode, where no updates are made and only the intended changes are reported.

        Note:
            - The matching is performed using the device_id field in both reported_measure and Gadget.
            - Gadget's device_id is not used as the 'name'; instead, Gadget's alias is used for 'name', and cliente for 'client'.
        """
        dry_run = options['dry_run']
        self.stdout.write(self.style.SUCCESS('Starting population of name and client fields from Gadget table...'))
        device_ids = reported_measure.objects.values_list('device_id', flat=True).distinct()
        gadget_map = {}
        for gadget in Gadget.objects.all():
            if gadget.device_id:
                gadget_map[gadget.device_id] = {
                    'name': gadget.alias or '',
                    'client': gadget.cliente or '',
                }
        self.stdout.write(f'Found {len(gadget_map)} matching device_ids in Gadget table')
        total_updated = 0
        for device_id, gadget_data in gadget_map.items():
            qs = reported_measure.objects.filter(device_id=device_id)
            count = qs.count()
            if not dry_run:
                qs.update(
                    name=gadget_data['name'],
                    client=gadget_data['client'],
                )
                self.stdout.write(f"  Updated {count} records for device_id: {device_id}")
            else:
                self.stdout.write(f"  Would update {count} records for device_id: {device_id}")
            total_updated += count
        if dry_run:
            self.stdout.write(self.style.WARNING(f'DRY RUN: Would have updated {total_updated} records'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Successfully updated {total_updated} records'))
