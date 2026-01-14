"""
Alert and Monitoring Service
Provides alerting functionality for disk space, device connections, and custom checks.
"""

import subprocess
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from django.conf import settings
from django.utils import timezone
from .models import AlertRule, Alert, AlertNotification


class AlertService:
    """Service for managing alerts and notifications"""
    
    def __init__(self):
        self.email_server = getattr(settings, 'ALERT_EMAIL_SERVER', 'mail.rggestionyenergia.com')
        self.email_port = getattr(settings, 'ALERT_EMAIL_PORT', 587)
        self.email_from = getattr(settings, 'ALERT_EMAIL_FROM', 'tecnico@rggestionyenergia.com')
        self.email_username = getattr(settings, 'ALERT_EMAIL_USERNAME', self.email_from)
        self.email_password = getattr(settings, 'ALERT_EMAIL_PASSWORD', '')
    
    def send_email_notification(self, recipients: str, subject: str, message: str) -> Dict:
        """
        Send email notification
        
        Args:
            recipients: Comma-separated email addresses
            subject: Email subject
            message: Email body
            
        Returns:
            Dict with 'success' (bool) and 'error' (str or None)
        """
        try:
            # Parse recipients
            recipient_list = [r.strip() for r in recipients.split(',') if r.strip()]
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = f"RGIoT <{self.email_from}>"
            msg['To'] = ', '.join(recipient_list)
            msg['Subject'] = subject
            
            msg.attach(MIMEText(message, 'plain', 'utf-8'))
            
            # Send email
            with smtplib.SMTP(self.email_server, self.email_port) as server:
                server.starttls()
                if self.email_password:
                    server.login(self.email_username, self.email_password)
                server.send_message(msg)
            
            return {'success': True, 'error': None}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def create_alert(self, rule: Optional[AlertRule], alert_type: str, message: str,
                    severity: str = 'warning', details: Dict = None) -> Alert:
        """
        Create a new alert
        
        Args:
            rule: AlertRule that triggered this alert (optional)
            alert_type: Type of alert (disk_space, device_connection, etc.)
            message: Alert message
            severity: Severity level (info, warning, error, critical)
            details: Additional details as dict
            
        Returns:
            Created Alert instance
        """
        alert = Alert.objects.create(
            rule=rule,
            alert_type=alert_type,
            severity=severity,
            message=message,
            details=details or {}
        )
        
        # Send notification if rule exists
        if rule and rule.active:
            self.send_alert_notification(alert, rule)
        
        return alert
    
    def send_alert_notification(self, alert: Alert, rule: AlertRule) -> AlertNotification:
        """
        Send notification for an alert based on rule configuration
        
        Args:
            alert: Alert instance
            rule: AlertRule with notification settings
            
        Returns:
            Created AlertNotification instance
        """
        subject = rule.notification_subject or f"[boreas] {alert.alert_type} Alert"
        
        notification = AlertNotification.objects.create(
            alert=alert,
            notification_type=rule.notification_type,
            recipients=rule.notification_recipients,
            subject=subject,
            message=alert.message
        )
        
        # Send based on notification type
        if rule.notification_type == 'email':
            result = self.send_email_notification(
                recipients=rule.notification_recipients,
                subject=subject,
                message=alert.message
            )
            
            if result['success']:
                notification.status = 'sent'
                notification.sent_at = timezone.now()
            else:
                notification.status = 'failed'
                notification.error_message = result['error']
            
            notification.save()
        
        return notification
    
    def check_generic_rule(self, rule: AlertRule) -> Optional[Alert]:
        """
        Generic alert trigger for any rule type.
        Creates an alert based on rule configuration without type-specific logic.
        
        Args:
            rule: AlertRule to check
            
        Returns:
            Alert if rule is configured to trigger, None otherwise
        """
        config = rule.config or {}
        
        # Check if rule is configured to trigger automatically
        auto_trigger = config.get('auto_trigger', True)  # Default: trigger on each check
        
        if auto_trigger:
            message = config.get('message', f"Alert triggered by rule: {rule.name}")
            severity = config.get('severity', 'warning')
            
            # Check if there's already an active alert for this rule (avoid duplicates)
            existing_active = Alert.objects.filter(
                rule=rule,
                alert_type=rule.rule_type,
                status='active'
            ).first()
            
            if existing_active:
                # Update timestamp instead of creating duplicate
                existing_active.triggered_at = timezone.now()
                existing_active.save(update_fields=['triggered_at'])
                return None
            
            return self.create_alert(
                rule=rule,
                alert_type=rule.rule_type,
                message=message,
                severity=severity,
                details=config.get('details', {})
            )
        
        return None
    
    def check_active_rules(self) -> List[Alert]:
        """
        Check all active alert rules and trigger alerts if needed
        
        Returns:
            List of triggered alerts
        """
        alerts = []
        active_rules = AlertRule.objects.filter(active=True)
        
        for rule in active_rules:
            # Check if it's time to run this rule
            if rule.last_check:
                next_check = rule.last_check + timedelta(minutes=rule.check_interval_minutes)
                if timezone.now() < next_check:
                    continue
            
            # Check based on rule type
            if rule.rule_type == 'disk_space':
                alert = self.check_disk_space_rule(rule)
            elif rule.rule_type == 'device_connection':
                alert = self.check_device_connection_rule(rule)
            else:
                # Generic fallback for any other rule type
                alert = self.check_generic_rule(rule)
            
            # Update last check time
            rule.last_check = timezone.now()
            rule.save(update_fields=['last_check'])
            
            if alert:
                alerts.append(alert)
        
        return alerts


class DiskSpaceAlertService(AlertService):
    """Service for disk space monitoring alerts"""
    
    def get_disk_usage_percent(self) -> Optional[int]:
        """
        Get disk usage percentage using df command
        
        Returns:
            Disk usage percentage (0-100) or None if error
        """
        try:
            # Run df command (works on Linux/Unix)
            cmd = "df -t ext4 --output=pcent | sed '2!d' | tr -d ' %\\n'"
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return int(result.stdout.strip())
            
            return None
        
        except Exception as e:
            print(f"Error getting disk usage: {e}")
            return None
    
    def check_disk_space_rule(self, rule: AlertRule) -> Optional[Alert]:
        """
        Check disk space against rule threshold
        
        Args:
            rule: AlertRule with disk_space type
            
        Returns:
            Alert if threshold exceeded, None otherwise
        """
        usage_percent = self.get_disk_usage_percent()
        
        if usage_percent is None:
            return None
        
        threshold = rule.threshold or 89
        
        if usage_percent >= threshold:
            message = f"""
El espacio de disco ocupado supera el {threshold}%
Usado: {usage_percent}%
            """.strip()
            
            # Check if there's already an active alert for this
            existing_active = Alert.objects.filter(
                rule=rule,
                alert_type='disk_space',
                status='active'
            ).first()
            
            if existing_active:
                # Update details instead of creating new alert
                existing_active.details['last_check'] = timezone.now().isoformat()
                existing_active.details['usage_percent'] = usage_percent
                existing_active.save()
                return None
            
            return self.create_alert(
                rule=rule,
                alert_type='disk_space',
                message=message,
                severity='critical' if usage_percent >= 95 else 'warning',
                details={
                    'usage_percent': usage_percent,
                    'threshold': threshold
                }
            )
        
        # Resolve any active alerts if usage is below threshold
        Alert.objects.filter(
            rule=rule,
            alert_type='disk_space',
            status='active'
        ).update(status='resolved', resolved_at=timezone.now())
        
        return None


class TopicTimeoutAlertService(AlertService):
    """Service for monitoring MQTT topic message timeouts"""
    
    def check_family_timeouts(self, rule: AlertRule) -> Optional[Alert]:
        """
        Check if a device family has not received messages within timeout period
        
        Args:
            rule: AlertRule with config containing 'family_name' and 'timeout_minutes'
            
        Returns:
            Alert instance if timeout detected, None otherwise
        """
        from .models import MQTT_device_family, mqtt_msg
        
        family_name = rule.config.get('family_name')
        timeout_minutes = rule.config.get('timeout_minutes', 60)
        
        if not family_name:
            print(f"Rule {rule.name} missing family_name in config")
            return None
        
        try:
            family = MQTT_device_family.objects.get(name=family_name)
        except MQTT_device_family.DoesNotExist:
            print(f"Family {family_name} not found")
            return None
        
        # Get last message for this family
        last_msg = mqtt_msg.objects.filter(device_family=family).order_by('-report_time').first()
        
        if not last_msg:
            # No messages ever received
            message = f"No data received from family '{family_name}' (never received any messages)"
            severity = 'critical'
        else:
            # Check timeout
            timeout_threshold = timezone.now() - timedelta(minutes=timeout_minutes)
            if last_msg.report_time < timeout_threshold:
                time_elapsed = (timezone.now() - last_msg.report_time).total_seconds() / 3600
                message = (
                    f"No data received from family '{family_name}' for {time_elapsed:.1f} hours\n"
                    f"Last message: {last_msg.report_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"Device: {last_msg.device_id}"
                )
                severity = 'warning'
            else:
                # Still receiving messages within timeout
                return None
        
        # Check if alert already exists and is still active
        existing_alert = Alert.objects.filter(
            rule=rule,
            alert_type='topic_timeout',
            status='active'
        ).first()
        
        if existing_alert:
            # Alert already sent, don't duplicate
            return None
        
        # Create new alert
        alert = self.create_alert(
            rule=rule,
            alert_type='topic_timeout',
            message=message,
            severity=severity,
            details={
                'family_name': family_name,
                'timeout_minutes': timeout_minutes,
                'last_message_time': last_msg.report_time.isoformat() if last_msg else None,
            }
        )
        
        # Send email notification if configured
        if rule.config.get('send_email') and rule.notification_recipients:
            self.send_email_notification(
                recipients=rule.notification_recipients,
                subject=rule.notification_subject or f"Alert: {family_name} - No data",
                message=message
            )
        
        return alert

    def check_api_timeout(self, rule: AlertRule) -> Optional[Alert]:
        """
        Check if an API source has not received data within timeout period
        
        Args:
            rule: AlertRule with config containing 'api_name', 'timeout_minutes', 'model'
            
        Returns:
            Alert instance if timeout detected, None otherwise
        """
        from datetime import timedelta, date
        from .models import SigfoxDevice, DatadisConsumption, DatadisMaxPower, WirelessLogic_SIM
        
        api_name = rule.config.get('api_name')
        timeout_minutes = rule.config.get('timeout_minutes', 60)
        model_name = rule.config.get('model')
        
        if not api_name or not model_name:
            print(f"Rule {rule.name} missing api_name or model in config")
            return None
        
        try:
            if model_name == 'SigfoxDevice':
                last_record = SigfoxDevice.objects.order_by('-updated_at').first()
                last_time = last_record.updated_at if last_record else None
            elif model_name == 'DatadisConsumption':
                last_record = DatadisConsumption.objects.order_by('-date', '-time').first()
                if last_record:
                    if isinstance(last_record.date, date):
                        last_time = timezone.make_aware(
                            timezone.datetime.combine(last_record.date, timezone.datetime.min.time())
                        )
                    else:
                        last_time = last_record.date
                else:
                    last_time = None
            elif model_name == 'DatadisMaxPower':
                last_record = DatadisMaxPower.objects.order_by('-date', '-time').first()
                if last_record:
                    if isinstance(last_record.date, date):
                        last_time = timezone.make_aware(
                            timezone.datetime.combine(last_record.date, timezone.datetime.min.time())
                        )
                    else:
                        last_time = last_record.date
                else:
                    last_time = None
            elif model_name == 'WirelessLogic_SIM':
                last_record = WirelessLogic_SIM.objects.order_by('-last_sync').first()
                last_time = last_record.last_sync if last_record else None
            else:
                print(f"Unknown model: {model_name}")
                return None
        except Exception as e:
            print(f"Error checking {api_name}: {str(e)}")
            return None
        
        if not last_time:
            # No data ever received
            message = f"No data received from '{api_name}' (never received any data)"
            severity = 'critical'
        else:
            # Check timeout
            timeout_threshold = timezone.now() - timedelta(minutes=timeout_minutes)
            if last_time < timeout_threshold:
                time_elapsed = (timezone.now() - last_time).total_seconds() / 3600
                message = (
                    f"No data received from '{api_name}' for {time_elapsed:.1f} hours\n"
                    f"Last update: {last_time.strftime('%Y-%m-%d %H:%M:%S')}"
                )
                severity = 'warning'
            else:
                # Still receiving data within timeout
                return None
        
        # Check if alert already exists and is still active
        existing_alert = Alert.objects.filter(
            rule=rule,
            alert_type='api_timeout',
            status='active'
        ).first()
        
        if existing_alert:
            # Alert already sent, don't duplicate
            return None
        
        # Create new alert
        alert = self.create_alert(
            rule=rule,
            alert_type='api_timeout',
            message=message,
            severity=severity,
            details={
                'api_name': api_name,
                'model': model_name,
                'timeout_minutes': timeout_minutes,
                'last_data_time': last_time.isoformat() if last_time else None,
            }
        )
        
        # Send email notification if configured
        if rule.config.get('send_email') and rule.notification_recipients:
            self.send_email_notification(
                recipients=rule.notification_recipients,
                subject=rule.notification_subject or f"Alert: {api_name} - No data",
                message=message
            )
        
        return alert


class DeviceConnectionAlertService(AlertService):
    """Service for device connection monitoring alerts"""
    
    def check_device_connection_rule(self, rule: AlertRule) -> Optional[Alert]:
        """
        Check device connections based on rule configuration
        
        Args:
            rule: AlertRule with device_connection type
            
        Returns:
            Alert if devices are disconnected, None otherwise
        """
        # This would query the database for device last update times
        # Based on the Node-RED flow: check if devices haven't updated in 12+ hours
        
        from .models import mqtt_msg
        
        config = rule.config or {}
        clients = config.get('clients', [])
        max_hours_inactive = config.get('max_hours_inactive', 12)
        
        if not clients:
            return None
        
        # Calculate cutoff time
        cutoff_time = timezone.now() - timedelta(hours=max_hours_inactive)
        
        # Find inactive devices
        inactive_devices = []
        for client in clients:
            devices = mqtt_msg.objects.filter(
                device__contains={'client': client}
            ).exclude(
                report_time__gte=cutoff_time
            )
            
            for device in devices:
                inactive_devices.append({
                    'device_id': device.device_id,
                    'client': client,
                    'last_seen': device.report_time.isoformat() if device.report_time else 'never'
                })
        
        if inactive_devices:
            device_list = '\n'.join([
                f"- {d['device_id']} (Cliente: {d['client']}, última vez: {d['last_seen']})"
                for d in inactive_devices
            ])
            
            message = f"""
¡¡ALARMA!! No hay recepción de datos

Se ha detectado que los siguientes dispositivos no envían datos desde hace más de {max_hours_inactive} horas:

{device_list}
            """.strip()
            
            return self.create_alert(
                rule=rule,
                alert_type='device_connection',
                message=message,
                severity='error',
                details={
                    'inactive_devices': inactive_devices,
                    'max_hours_inactive': max_hours_inactive
                }
            )
        
        return None
