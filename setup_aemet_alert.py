#!/usr/bin/env python
"""
Script to create AEMET data monitoring alert rule
Run this after the model migration
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'boreas_mediacion.settings')
django.setup()

from boreas_mediacion.models import AlertRule

# Create AEMET monitoring alert rule
rule, created = AlertRule.objects.get_or_create(
    name='AEMET Weather Data Monitor',
    rule_type='aemet_data',
    defaults={
        'description': 'Monitors for new AEMET weather data arrivals and sends email notifications',
        'check_interval_minutes': 5,
        'notification_type': 'email',
        'notification_recipients': 'alonsogpablo@gestionyenergia.com',
        'notification_subject': '🌤️ AEMET Weather Data Arrival Notification',
        'active': True,
        'config': {
            'check_minutes': 5,
            'send_summary': True
        }
    }
)

if created:
    print(f"✅ Created AEMET alert rule: {rule.name}")
else:
    print(f"ℹ️  AEMET alert rule already exists: {rule.name}")
    
print(f"\nRule details:")
print(f"  - Type: {rule.get_rule_type_display()}")
print(f"  - Check interval: Every {rule.check_interval_minutes} minutes")
print(f"  - Recipients: {rule.notification_recipients}")
print(f"  - Active: {rule.active}")
