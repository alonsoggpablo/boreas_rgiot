from django.core.management.base import BaseCommand
## ALERT SERVICE REMOVED: All alerting is now handled by Prometheus metrics
from boreas_mediacion.models import AlertRule
from django.utils import timezone


class Command(BaseCommand):
    help = 'Check alert rules and trigger alerts if needed'

    def add_arguments(self, parser):
        parser.add_argument(
            'rule_type',
            type=str,
            nargs='?',
            default='all',
            help='Rule type to check: disk_space, device_connection, or all'
        )

    def handle(self, *args, **options):
        rule_type = options['rule_type']
        
        self.stdout.write(f"\nChecking alert rules: {rule_type}")
        self.stdout.write("=" * 60)
        
        disk_service = DiskSpaceAlertService()
        device_service = DeviceConnectionAlertService()
        generic_service = AlertService()
        
        results = {
            'checked': 0,
            'alerts_triggered': 0,
            'errors': 0,
            'details': []
        }
        
        # Get active rules
        rules = AlertRule.objects.filter(active=True)
        
        if rule_type != 'all':
            rules = rules.filter(rule_type=rule_type)
        
        for rule in rules:
            try:
                results['checked'] += 1
                alert = None
                
                self.stdout.write(f"\n📋 Checking: {rule.name}")
                self.stdout.write(f"   Type: {rule.get_rule_type_display()}")
                self.stdout.write(f"   Interval: {rule.check_interval_minutes} minutes")
                
                # Check if it's time to run
                if rule.last_check:
                    minutes_since = (timezone.now() - rule.last_check).total_seconds() / 60
                    if minutes_since < rule.check_interval_minutes:
                        self.stdout.write(
                            f"   ⏭️  Skipped (last check {int(minutes_since)} min ago)"
                        )
                        continue
                
                # Execute check
                if rule.rule_type == 'disk_space':
                    alert = disk_service.check_disk_space_rule(rule)
                elif rule.rule_type == 'device_connection':
                    alert = device_service.check_device_connection_rule(rule)
                else:
                    # Generic trigger for any other rule type
                    alert = generic_service.check_generic_rule(rule)
                
                # Update last check
                rule.last_check = timezone.now()
                rule.save(update_fields=['last_check'])
                
                # Report result
                if alert:
                    results['alerts_triggered'] += 1
                    self.stdout.write(
                        self.style.WARNING(f"   🚨 ALERT TRIGGERED (ID: {alert.id})")
                    )
                    self.stdout.write(f"   Severity: {alert.severity}")
                    self.stdout.write(f"   Message: {alert.message[:80]}...")
                    
                    # Check notifications
                    notifs = alert.notifications.all()
                    for notif in notifs:
                        status_icon = "✓" if notif.status == 'sent' else "⏳"
                        self.stdout.write(
                            f"   {status_icon} Notification: {notif.notification_type} "
                            f"({notif.status})"
                        )
                    
                    results['details'].append({
                        'rule': rule.name,
                        'alert_id': alert.id,
                        'severity': alert.severity,
                        'status': 'triggered'
                    })
                else:
                    self.stdout.write(
                        self.style.SUCCESS(f"   ✓ OK - No alert triggered")
                    )
                    results['details'].append({
                        'rule': rule.name,
                        'status': 'ok'
                    })
            
            except Exception as e:
                results['errors'] += 1
                self.stdout.write(
                    self.style.ERROR(f"   ✗ ERROR: {str(e)}")
                )
                results['details'].append({
                    'rule': rule.name,
                    'status': 'error',
                    'error': str(e)
                })
        
        # Summary
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("SUMMARY")
        self.stdout.write("=" * 60)
        self.stdout.write(f"Rules checked: {results['checked']}")
        self.stdout.write(f"Alerts triggered: {results['alerts_triggered']}")
        self.stdout.write(f"Errors: {results['errors']}")
        
        if results['alerts_triggered'] > 0:
            self.stdout.write(
                self.style.WARNING(f"\n⚠️  {results['alerts_triggered']} alert(s) triggered")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS("\n✓ All checks passed, no alerts")
            )
        
        self.stdout.write("")
