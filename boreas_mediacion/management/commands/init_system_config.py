"""
Django management command to initialize system configuration
"""
from django.core.management.base import BaseCommand
from boreas_mediacion.models import SystemConfiguration


class Command(BaseCommand):
    help = 'Initialize system configuration with default values'

    def handle(self, *args, **options):
        """Create initial system configuration entries"""
        
        configs = [
            {
                'key': 'airflow_failure_email',
                'value': 'alonsogpablo@rggestionyenergia.com',
                'config_type': 'airflow',
                'description': 'Email para notificaciones de fallo de Airflow DAGs'
            },
            {
                'key': 'aemet_alert_email',
                'value': 'alonsogpablo@rggestionyenergia.com',
                'config_type': 'alert',
                'description': 'Email para alertas de datos AEMET'
            },
            {
                'key': 'default_alert_recipients',
                'value': 'alonsogpablo@rggestionyenergia.com',
                'config_type': 'alert',
                'description': 'Destinatarios por defecto para alertas del sistema (separados por comas)'
            },
        ]
        
        created_count = 0
        updated_count = 0
        
        for config_data in configs:
            config, created = SystemConfiguration.objects.update_or_create(
                key=config_data['key'],
                defaults={
                    'value': config_data['value'],
                    'config_type': config_data['config_type'],
                    'description': config_data['description'],
                    'active': True
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created: {config_data["key"]} = {config_data["value"]}')
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'→ Updated: {config_data["key"]} = {config_data["value"]}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Configuration initialized: {created_count} created, {updated_count} updated'
            )
        )
