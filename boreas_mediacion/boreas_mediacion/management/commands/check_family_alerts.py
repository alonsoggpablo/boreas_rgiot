#!/usr/bin/env python
"""
Management command to check and trigger family and API timeout alerts.
Run this periodically (e.g., every 10 minutes via cron or Airflow).
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from boreas_mediacion.models import AlertRule, Alert
## ALERT SERVICE REMOVED: All alerting is now handled by Prometheus metrics


class Command(BaseCommand):
    help = 'Check family and API timeout alert rules and trigger alerts if needed'

    def handle(self, *args, **options):
        service = TopicTimeoutAlertService()
        
        # Get all active timeout rules (both family and API)
        rules = AlertRule.objects.filter(
            rule_type__in=[
                'topic_message_timeout',
                'api_sigfox',
                'api_datadis_consumption',
                'api_datadis_power',
                'api_wirelesslogic',
            ],
            active=True
        )
        
        if not rules.exists():
            self.stdout.write(self.style.WARNING("No timeout alert rules found"))
            return
        
        self.stdout.write(f"Checking {rules.count()} timeout rules...")
        
        alerts_triggered = 0
        for rule in rules:
            # Update last check time
            rule.last_check = timezone.now()
            rule.save()
            
            # Check for timeout based on rule type
            if rule.rule_type == 'topic_message_timeout':
                alert = service.check_family_timeouts(rule)
            else:
                # API timeout
                alert = service.check_api_timeout(rule)
            
            if alert:
                alerts_triggered += 1
                self.stdout.write(
                    self.style.WARNING(
                        f"✗ ALERT TRIGGERED: {rule.name}\n  Message: {alert.message[:100]}..."
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f"✓ OK: {rule.name}")
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Check completed. {alerts_triggered} alert(s) triggered.'
            )
        )
