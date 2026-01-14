#!/usr/bin/env python
"""
Management command to create alert rules for each MQTT device family.
Sends alert if no data received in 1 hour.
"""
from django.core.management.base import BaseCommand
from boreas_mediacion.models import AlertRule, MQTT_device_family, SystemConfiguration


class Command(BaseCommand):
    help = 'Create alert rules for each MQTT device family (1 hour timeout)'

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
                'family_alert_email',
                'alonsogpablo@rggestionyenergia.com'
            )
        
        families = MQTT_device_family.objects.all()
        created_count = 0
        
        for family in families:
            rule_name = f"No data from {family.name} for 1 hour"
            
            # Check if rule already exists
            existing_rule = AlertRule.objects.filter(
                name=rule_name,
                rule_type='topic_message_timeout'
            ).exists()
            
            if existing_rule:
                self.stdout.write(
                    self.style.WARNING(f"Rule already exists: {rule_name}")
                )
                continue
            
            # Create alert rule
            rule = AlertRule.objects.create(
                name=rule_name,
                rule_type='topic_message_timeout',
                description=f'Alert if no messages received from {family.name} family for 1 hour',
                check_interval_minutes=10,  # Check every 10 minutes
                notification_type='email',
                notification_recipients=email,
                notification_subject=f'Alert: No data from {family.name}',
                active=True,
                config={
                    'family_name': family.name,
                    'timeout_minutes': 60,
                    'send_email': True,
                }
            )
            
            created_count += 1
            self.stdout.write(
                self.style.SUCCESS(f'✓ Created rule: {rule_name}')
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'\n✓ Successfully created {created_count} alert rules')
        )
