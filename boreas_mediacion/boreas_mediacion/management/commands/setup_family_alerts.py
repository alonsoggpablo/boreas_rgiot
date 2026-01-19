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
        
        # Create disk usage alert rule
        disk_rule_name = "Host disk usage over 70%"
        if not AlertRule.objects.filter(name=disk_rule_name, rule_type='disk_space').exists():
            AlertRule.objects.create(
                name=disk_rule_name,
                rule_type='disk_space',
                description='Alert if host disk usage exceeds 70%',
                threshold=70,
                check_interval_minutes=60,
                notification_type='email',
                notification_recipients=email,
                notification_subject='Alert: Host disk usage over 70%',
                active=True,
                config={'send_email': True}
            )
            self.stdout.write(self.style.SUCCESS(f'✓ Created rule: {disk_rule_name}'))
        else:
            self.stdout.write(self.style.WARNING(f'Rule already exists: {disk_rule_name}'))

        # Create RAM usage alert rule
        ram_rule_name = "Host RAM usage over 70%"
        if not AlertRule.objects.filter(name=ram_rule_name, rule_type='custom').exists():
            AlertRule.objects.create(
                name=ram_rule_name,
                rule_type='custom',
                description='Alert if host RAM usage exceeds 70%',
                threshold=70,
                check_interval_minutes=60,
                notification_type='email',
                notification_recipients=email,
                notification_subject='Alert: Host RAM usage over 70%',
                active=True,
                config={'check_type': 'ram', 'send_email': True}
            )
            self.stdout.write(self.style.SUCCESS(f'✓ Created rule: {ram_rule_name}'))
        else:
            self.stdout.write(self.style.WARNING(f'Rule already exists: {ram_rule_name}'))

        self.stdout.write(
            self.style.SUCCESS(f'\n✓ Successfully created {created_count} alert rules')
        )
