"""
Celery tasks for alert monitoring
"""

from celery import shared_task
from django.utils import timezone
from .alert_service import DiskSpaceAlertService, DeviceConnectionAlertService
from .models import AlertRule


@shared_task
def check_all_alert_rules():
    """
    Check all active alert rules and trigger alerts if needed.
    This task should be run periodically (e.g., every 5-10 minutes)
    """
    disk_service = DiskSpaceAlertService()
    device_service = DeviceConnectionAlertService()
    
    alerts_triggered = []
    
    # Get all active rules
    active_rules = AlertRule.objects.filter(active=True)
    
    for rule in active_rules:
        try:
            # Check if it's time to run this rule based on check_interval_minutes
            if rule.last_check:
                minutes_since_last_check = (timezone.now() - rule.last_check).total_seconds() / 60
                if minutes_since_last_check < rule.check_interval_minutes:
                    continue
            
            # Check based on rule type
            alert = None
            if rule.rule_type == 'disk_space':
                alert = disk_service.check_disk_space_rule(rule)
            elif rule.rule_type == 'device_connection':
                alert = device_service.check_device_connection_rule(rule)
            
            # Update last check time
            rule.last_check = timezone.now()
            rule.save(update_fields=['last_check'])
            
            if alert:
                alerts_triggered.append({
                    'rule': rule.name,
                    'alert_id': alert.id,
                    'severity': alert.severity,
                    'message': alert.message[:100]
                })
        
        except Exception as e:
            print(f"Error checking rule {rule.name}: {e}")
    
    return {
        'checked': active_rules.count(),
        'alerts_triggered': len(alerts_triggered),
        'alerts': alerts_triggered
    }


@shared_task
def check_disk_space():
    """
    Dedicated task to check disk space.
    Runs daily at 10:00 (configured in Celery Beat schedule)
    """
    service = DiskSpaceAlertService()
    
    # Get active disk space rules
    rules = AlertRule.objects.filter(active=True, rule_type='disk_space')
    
    results = []
    for rule in rules:
        try:
            alert = service.check_disk_space_rule(rule)
            rule.last_check = timezone.now()
            rule.save(update_fields=['last_check'])
            
            if alert:
                results.append({
                    'rule': rule.name,
                    'alert_triggered': True,
                    'severity': alert.severity
                })
            else:
                results.append({
                    'rule': rule.name,
                    'alert_triggered': False
                })
        except Exception as e:
            results.append({
                'rule': rule.name,
                'error': str(e)
            })
    
    return results


@shared_task
def check_device_connections():
    """
    Dedicated task to check device connections.
    Runs daily at 09:00 (configured in Celery Beat schedule)
    """
    service = DeviceConnectionAlertService()
    
    # Get active device connection rules
    rules = AlertRule.objects.filter(active=True, rule_type='device_connection')
    
    results = []
    for rule in rules:
        try:
            alert = service.check_device_connection_rule(rule)
            rule.last_check = timezone.now()
            rule.save(update_fields=['last_check'])
            
            if alert:
                results.append({
                    'rule': rule.name,
                    'alert_triggered': True,
                    'inactive_devices': len(alert.details.get('inactive_devices', []))
                })
            else:
                results.append({
                    'rule': rule.name,
                    'alert_triggered': False
                })
        except Exception as e:
            results.append({
                'rule': rule.name,
                'error': str(e)
            })
    
    return results


@shared_task
def cleanup_old_alerts(days=30):
    """
    Clean up resolved alerts older than specified days
    
    Args:
        days: Number of days to keep resolved alerts (default 30)
    """
    from datetime import timedelta
    from .models import Alert
    
    cutoff_date = timezone.now() - timedelta(days=days)
    
    # Delete resolved alerts older than cutoff
    deleted_count, _ = Alert.objects.filter(
        status='resolved',
        resolved_at__lt=cutoff_date
    ).delete()
    
    return {
        'deleted_alerts': deleted_count,
        'cutoff_date': cutoff_date.isoformat()
    }
