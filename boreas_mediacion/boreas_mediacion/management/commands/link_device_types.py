from django.core.management.base import BaseCommand, CommandError
from boreas_mediacion.models import MQTT_device_family


class Command(BaseCommand):
    help = 'Link external device types to MQTT device families'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview links without saving'
        )
        parser.add_argument(
            '--device-type',
            type=str,
            help='Link specific device type (e.g., "Router")'
        )
        parser.add_argument(
            '--family',
            type=str,
            help='Target MQTT device family name (e.g., "routers")'
        )
        parser.add_argument(
            '--list-families',
            action='store_true',
            help='List all available MQTT device families'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        device_type = options.get('device_type')
        family_name = options.get('family')
        list_families = options.get('list_families')

        # Show available families if requested
        if list_families:
            self.show_available_families()
            return

        # Define default mappings: external_type -> mqtt_family_name
        default_mappings = {
            'Router': 'router',
            'Nanoenvi IAQ': 'IAQ_Measures',
            'Nanoenvi Noise': 'IAQ_Measures',
            'Contador Gas': 'EM_Measures',
            'DATADIS': 'EM_Measures',
            'Punto': 'RPC',
            'Meter': 'EM_Measures',
            'Water Meter': 'EM_Measures',
            'CO2': 'co2',
        }

        # If specific device type and family provided, link that one
        if device_type and family_name:
            self.link_single_device_type(device_type, family_name, dry_run)
            return

        # Otherwise, apply default mappings
        self.apply_default_mappings(default_mappings, dry_run)

    def show_available_families(self):
        """Display all available MQTT device families"""
        families = MQTT_device_family.objects.all().order_by('name')
        
        if not families.exists():
            self.stdout.write(self.style.WARNING('No MQTT device families found in database'))
            return

        self.stdout.write(self.style.SUCCESS('\n📋 Available MQTT Device Families:\n'))
        for family in families:
            
        self.stdout.write('')

    def link_single_device_type(self, device_type, family_name, dry_run):
        """Link a single device type to a family"""
        

        try:
            family = MQTT_device_family.objects.get(name=family_name)
        except MQTT_device_family.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'✗ MQTT family "{family_name}" not found')
            )
            self.show_available_families()
            return

        if not dry_run:
            device_mapping.mqtt_device_family = family
            device_mapping.save()

        self.stdout.write(
            self.style.SUCCESS(f'✓ Linked "{device_type}" → "{family_name}"')
        )

    def apply_default_mappings(self, mappings, dry_run):
        """Apply default device type to family mappings"""
        updated = 0
        not_found_types = []
        not_found_families = []

        self.stdout.write(self.style.SUCCESS('\n🔗 Linking Device Types to MQTT Families:\n'))

        for external_type, family_name in mappings.items():
            try:
                device_mapping = DeviceTypeMapping.objects.get(external_device_type_name=external_type)
                try:
                    family = MQTT_device_family.objects.get(name=family_name)
                    
                    if not dry_run:
                        device_mapping.mqtt_device_family = family
                        device_mapping.save()
                        
                    self.stdout.write(
                        self.style.SUCCESS(f'  ✓ {external_type:25} → {family_name}')
                    )
                    updated += 1
                except MQTT_device_family.DoesNotExist:
                    not_found_families.append((external_type, family_name))
                    self.stdout.write(
                        self.style.WARNING(f'  ⚠ {external_type:25} → {family_name} (family not found)')
                    )
            except DeviceTypeMapping.DoesNotExist:
                not_found_types.append(external_type)
                self.stdout.write(
                    self.style.WARNING(f'  ⚠ {external_type:25} (device type not found)')
                )

        self.stdout.write('')

        # Summary
        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'[DRY RUN] Would update {updated} mappings')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'✓ Successfully linked {updated} device type(s)')
            )

        if not_found_types:
            self.stdout.write(
                self.style.WARNING(f'\n⚠ Device types not found: {", ".join(not_found_types)}')
            )

        if not_found_families:
            self.stdout.write(
                self.style.WARNING(f'\n⚠ MQTT families not found:')
            )
            for external_type, family_name in not_found_families:
                self.stdout.write(f'  • {family_name} (for {external_type})')
            self.show_available_families()

        self.stdout.write('')
