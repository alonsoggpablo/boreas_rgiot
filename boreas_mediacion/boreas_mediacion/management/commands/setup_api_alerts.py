#!/usr/bin/env python
"""
Management command to create alert rules for API sources.
Sends alert if no data received in 1 hour.
"""
from django.core.management.base import BaseCommand
from boreas_mediacion.models import AlertRule, SystemConfiguration


class Command(BaseCommand):
    help = 'Create alert rules for API sources (1 hour timeout)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            default=None,
            help='Email address to send alerts to (uses system config if not provided)',
        )

    def handle(self, *args, **options):
        # Get email from argument or system config
        email = options.get('email')
        if not email:
            email = SystemConfiguration.get_value(
                'api_alert_email',
                'alonsogpablo@rggestionyenergia.com'
            )
        
        # API sources to monitor
        api_sources = [
            {
                'name': 'Sigfox',
                'type': 'api_sigfox',
                'config_key': 'sigfox',
                'model': 'SigfoxDevice',
            },
            {
                'name': 'DATADIS Consumption',
                'type': 'api_datadis_consumption',
                'config_key': 'datadis_consumption',
                'model': 'DatadisConsumption',
            },
            {
                'name': 'DATADIS Max Power',
                'type': 'api_datadis_power',
                'config_key': 'datadis_power',
                'model': 'DatadisMaxPower',
            },
            {
                'name': 'WirelessLogic',
                'type': 'api_wirelesslogic',
                'config_key': 'wirelesslogic',
                'model': 'WirelessLogic_SIM',
            },
        ]
        
        created_count = 0
        
        for api in api_sources:
            rule_name = f"No data from {api['name']} for 1 hour"
            
            # Check if rule already exists
            existing_rule = AlertRule.objects.filter(
                name=rule_name,
                rule_type=api['type']
            ).exists()
            
            if existing_rule:
                self.stdout.write(
                    self.style.WARNING(f"Rule already exists: {rule_name}")
                )
                continue
            
            # Create alert rule
            rule = AlertRule.objects.create(
                name=rule_name,
                rule_type=api['type'],
                description=f'Alert if no data received from {api["name"]} API for 1 hour',
                check_interval_minutes=10,  # Check every 10 minutes
                notification_type='email',
                notification_recipients=email,
                notification_subject=f'Alert: No data from {api["name"]}',
                active=True,
                config={
                    'api_name': api['name'],
                    'timeout_minutes': 60,
                    'send_email': True,
                    'model': api['model'],
                }
            )
            
            created_count += 1
            self.stdout.write(
                self.style.SUCCESS(f'✓ Created rule: {rule_name}')
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'\n✓ Successfully created {created_count} API alert rules')
        )
