"""
Test alert system - Create alert rules and test notifications
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'boreas_mediacion.settings')
django.setup()

from boreas_mediacion.models import AlertRule
from boreas_mediacion.alert_service import DiskSpaceAlertService

def create_test_alert_rules():
    """Create test alert rules"""
    
    print("\n" + "="*60)
    print("CREATING TEST ALERT RULES")
    print("="*60 + "\n")
    
    # Rule 1: Disk Space Alert
    disk_rule, created = AlertRule.objects.get_or_create(
        name='Disk Space Monitor',
        defaults={
            'rule_type': 'disk_space',
            'description': 'Monitor disk space usage and alert if exceeds threshold',
            'threshold': 89,
            'check_interval_minutes': 60,
            'notification_type': 'email',
            'notification_recipients': 'tecnico@rggestionyenergia.com',
            'notification_subject': '[boreas] Alerta de espacio',
            'active': True,
            'config': {
                'filesystem': 'ext4',
                'critical_threshold': 95
            }
        }
    )
    
    if created:
        print(f"✓ Created: {disk_rule.name}")
        print(f"  Type: {disk_rule.get_rule_type_display()}")
        print(f"  Threshold: {disk_rule.threshold}%")
        print(f"  Recipients: {disk_rule.notification_recipients}")
    else:
        print(f"✓ Exists: {disk_rule.name}")
    
    # Rule 2: Device Connection Alert (example, will be disabled)
    device_rule, created = AlertRule.objects.get_or_create(
        name='Device Connection Monitor - Madrid',
        defaults={
            'rule_type': 'device_connection',
            'description': 'Monitor device connections from Madrid clients',
            'check_interval_minutes': 60,
            'notification_type': 'email',
            'notification_recipients': 'tecnico@esipe.com,gestion@rggestionyenergia.com,tecnico@rggestionyenergia.com',
            'notification_subject': '¡¡ALARMA!! No hay recepción de datos',
            'active': False,  # Disabled by default
            'config': {
                'clients': ['Metro de Madrid', 'Ayuntamiento de Madrid'],
                'max_hours_inactive': 12
            }
        }
    )
    
    if created:
        print(f"✓ Created: {device_rule.name}")
        print(f"  Type: {device_rule.get_rule_type_display()}")
        print(f"  Status: DISABLED (needs device setup)")
        print(f"  Recipients: {device_rule.notification_recipients}")
    else:
        print(f"✓ Exists: {device_rule.name}")
    
    print(f"\n✓ Alert rules ready in database")
    return disk_rule, device_rule


def test_disk_space_check():
    """Test disk space checking"""
    
    print("\n" + "="*60)
    print("TESTING DISK SPACE CHECK")
    print("="*60 + "\n")
    
    service = DiskSpaceAlertService()
    disk_rule = AlertRule.objects.get(name='Disk Space Monitor')
    
    # Get current disk usage
    usage = service.get_disk_usage_percent()
    
    if usage is not None:
        print(f"✓ Current disk usage: {usage}%")
        print(f"  Threshold: {disk_rule.threshold}%")
        
        if usage >= disk_rule.threshold:
            print(f"  ⚠ WARNING: Disk usage exceeds threshold!")
        else:
            print(f"  ✓ OK: Disk usage below threshold")
    else:
        print("✗ Could not determine disk usage (running on non-Linux system)")
        return
    
    # Simulate a check (with lower threshold for testing)
    print(f"\nSimulating check with threshold...")
    
    # Create a temporary rule with lower threshold for testing
    test_rule, _ = AlertRule.objects.get_or_create(
        name='Test Disk Alert (Low Threshold)',
        defaults={
            'rule_type': 'disk_space',
            'description': 'Test rule for demonstration',
            'threshold': 1,  # Very low threshold to trigger alert
            'check_interval_minutes': 1,
            'notification_type': 'email',
            'notification_recipients': 'tecnico@rggestionyenergia.com',
            'notification_subject': '[boreas TEST] Alerta de espacio',
            'active': True,
        }
    )
    
    alert = service.check_disk_space_rule(test_rule)
    
    if alert:
        print(f"\n✓ Alert triggered successfully!")
        print(f"  Alert ID: {alert.id}")
        print(f"  Severity: {alert.severity}")
        print(f"  Message: {alert.message[:100]}...")
        print(f"  Status: {alert.status}")
        
        # Check notifications
        notifications = alert.notifications.all()
        if notifications.exists():
            for notif in notifications:
                print(f"\n  Notification created:")
                print(f"    Type: {notif.notification_type}")
                print(f"    Recipients: {notif.recipients[:50]}...")
                print(f"    Status: {notif.status}")
                if notif.error_message:
                    print(f"    Error: {notif.error_message}")
    else:
        print(f"✗ No alert triggered (disk usage below test threshold)")


def display_summary():
    """Display summary of alert system"""
    
    print("\n" + "="*60)
    print("ALERT SYSTEM SUMMARY")
    print("="*60 + "\n")
    
    from boreas_mediacion.models import Alert, AlertNotification
    
    rules = AlertRule.objects.all()
    alerts = Alert.objects.all()
    notifications = AlertNotification.objects.all()
    
    print(f"Alert Rules: {rules.count()}")
    for rule in rules:
        status = "✓ ACTIVE" if rule.active else "✗ INACTIVE"
        print(f"  - {rule.name} ({rule.get_rule_type_display()}) {status}")
    
    print(f"\nAlerts: {alerts.count()}")
    for alert in alerts.order_by('-triggered_at')[:5]:
        print(f"  - [{alert.severity.upper()}] {alert.alert_type} @ {alert.triggered_at.strftime('%Y-%m-%d %H:%M')}")
        print(f"    Status: {alert.status}")
    
    print(f"\nNotifications: {notifications.count()}")
    for notif in notifications.order_by('-created_at')[:3]:
        print(f"  - {notif.notification_type} to {notif.recipients[:40]}... ({notif.status})")
    
    print(f"\n✓ Alert system fully operational")
    print(f"  - Admin interface: /admin/boreas_mediacion/alertrule/")
    print(f"  - Monitor alerts: /admin/boreas_mediacion/alert/")
    print(f"  - Check notifications: /admin/boreas_mediacion/alertnotification/")


if __name__ == '__main__':
    try:
        # Create test alert rules
        disk_rule, device_rule = create_test_alert_rules()
        
        # Test disk space check
        test_disk_space_check()
        
        # Display summary
        display_summary()
        
        print(f"\n✓ Alert system test completed successfully!")
        
    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
