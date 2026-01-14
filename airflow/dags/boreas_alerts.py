"""
Boreas Alert Monitoring DAG

Orchestrates alert checking using Apache Airflow:
- Disk space monitoring (daily at 10:00)
- Device connection monitoring (daily at 09:00)
- Alert cleanup (daily at 02:00)
"""
import sys
import os

# Add Django project to Python path FIRST, before any imports
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'boreas_mediacion.settings')

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago

def get_airflow_email():
    """Get Airflow failure notification email from database"""
    import os
    import django
    
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'boreas_mediacion.settings')
    django.setup()
    
    from boreas_mediacion.models import SystemConfiguration
    
    email = SystemConfiguration.get_value('airflow_failure_email', 'alonsogpablo@rggestionyenergia.com')
    return [email]

# Default DAG arguments
default_args = {
    'owner': 'boreas',
    'depends_on_past': False,
    'start_date': days_ago(1),
    'email': get_airflow_email(),
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

# DAG definition
dag = DAG(
    'boreas_alerts',
    default_args=default_args,
    description='Boreas Alert Monitoring System',
    schedule_interval='0 2,9,10 * * *',  # 02:00, 09:00, 10:00 daily
    catchup=False,
    tags=['boreas', 'alerts', 'monitoring'],
)


def check_alert_rule_type(rule_type: str):
    """
    Python function to check specific alert rule type
    
    Args:
        rule_type: Type of alert rule to check (disk_space, device_connection, cleanup)
    """
    import os
    import sys
    import django
    
    # Setup Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'boreas_mediacion.settings')
    sys.path.insert(0, '/app')
    django.setup()
    
    from boreas_mediacion.models import AlertRule
    from boreas_mediacion.alert_service import (
        DiskSpaceAlertService, 
        DeviceConnectionAlertService,
        AlertService
    )
    from django.utils import timezone
    
    print(f"\n{'='*60}")
    print(f"Checking alert rule: {rule_type}")
    print(f"{'='*60}\n")
    
    disk_service = DiskSpaceAlertService()
    device_service = DeviceConnectionAlertService()
    generic_service = AlertService()
    
    alerts_triggered = 0
    rules_checked = 0
    
    if rule_type == 'cleanup':
        # Special case: cleanup old alerts
        from boreas_mediacion.models import Alert
        cutoff_date = timezone.now() - timedelta(days=30)
        deleted_count, _ = Alert.objects.filter(
            status='resolved',
            resolved_at__lt=cutoff_date
        ).delete()
        print(f"✓ Cleaned up {deleted_count} old alerts")
        return
    
    # Get active rules of the specified type
    rules = AlertRule.objects.filter(active=True, rule_type=rule_type)
    
    for rule in rules:
        rules_checked += 1
        print(f"📋 Checking: {rule.name}")
        print(f"   Type: {rule.get_rule_type_display()}")
        
        try:
            alert = None
            
            # Check if it's time to run
            if rule.last_check:
                minutes_since = (timezone.now() - rule.last_check).total_seconds() / 60
                if minutes_since < rule.check_interval_minutes:
                    print(f"   ⏭️  Skipped (last check {int(minutes_since)} min ago)")
                    continue
            
            # Execute check
            if rule.rule_type == 'disk_space':
                alert = disk_service.check_disk_space_rule(rule)
            elif rule.rule_type == 'device_connection':
                alert = device_service.check_device_connection_rule(rule)
            else:
                # Generic trigger for any other rule type (aemet_data, custom, etc.)
                alert = generic_service.check_generic_rule(rule)
            
            # Update last check
            rule.last_check = timezone.now()
            rule.save(update_fields=['last_check'])
            
            # Report result
            if alert:
                alerts_triggered += 1
                print(f"   🚨 ALERT TRIGGERED (ID: {alert.id})")
                print(f"   Severity: {alert.severity}")
                print(f"   Message: {alert.message[:100]}...")
                
                # Check notifications
                for notif in alert.notifications.all():
                    status = "✓" if notif.status == 'sent' else "⏳"
                    print(f"   {status} {notif.notification_type}: {notif.status}")
            else:
                print(f"   ✓ OK - No alert triggered")
        
        except Exception as e:
            print(f"   ✗ ERROR: {str(e)}")
            raise
    
    # Summary
    print(f"\n{'='*60}")
    print(f"Summary: {rules_checked} rule(s) checked, {alerts_triggered} alert(s) triggered")
    print(f"{'='*60}\n")


# Task: Cleanup old alerts (02:00)
cleanup_alerts = PythonOperator(
    task_id='cleanup_old_alerts',
    python_callable=check_alert_rule_type,
    op_kwargs={'rule_type': 'cleanup'},
    dag=dag,
)

# Task: Check device connections (09:00)
check_device_connections = PythonOperator(
    task_id='check_device_connections',
    python_callable=check_alert_rule_type,
    op_kwargs={'rule_type': 'device_connection'},
    dag=dag,
)

# Task: Check disk space (10:00)
check_disk_space = PythonOperator(
    task_id='check_disk_space',
    python_callable=check_alert_rule_type,
    op_kwargs={'rule_type': 'disk_space'},
    dag=dag,
)

# Task dependencies
cleanup_alerts >> check_device_connections >> check_disk_space
