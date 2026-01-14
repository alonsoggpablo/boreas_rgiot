#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'boreas_mediacion.settings')
django.setup()

from boreas_mediacion.models import AlertRule

rule = AlertRule.objects.get(name='AEMET Weather Data Monitor')
rule.config = {
    'auto_trigger': True,
    'message': 'AEMET weather data has arrived',
    'severity': 'info',
    'details': {'source': 'aemet'}
}
rule.save()

print(f'✓ Updated AEMET rule config:')
print(f'  auto_trigger: {rule.config["auto_trigger"]}')
print(f'  message: {rule.config["message"]}')
print(f'  severity: {rule.config["severity"]}')
print(f'  active: {rule.active}')
print(f'  recipients: {rule.notification_recipients}')
