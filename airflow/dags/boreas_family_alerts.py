"""
Airflow DAG to check family timeout alerts every 10 minutes
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
import os
import sys
import django

# Add the Django project to the path
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'boreas_mediacion.settings')
django.setup()

from boreas_mediacion.models import AlertRule, Alert
from boreas_mediacion.alert_service import TopicTimeoutAlertService


def check_family_alerts():
    """Check family timeout alert rules"""
    service = TopicTimeoutAlertService()
    
    # Get all active topic_message_timeout rules
    rules = AlertRule.objects.filter(
        rule_type='topic_message_timeout',
        active=True
    )
    
    alerts_triggered = 0
    for rule in rules:
        # Check for timeout
        alert = service.check_family_timeouts(rule)
        
        if alert:
            alerts_triggered += 1
            print(f"ALERT TRIGGERED: {rule.name}")
    
    print(f"Family alert check completed. {alerts_triggered} alert(s) triggered.")
    return alerts_triggered


default_args = {
    'owner': 'boreas',
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
}

dag = DAG(
    'boreas_family_alerts',
    default_args=default_args,
    description='Check family timeout alerts every 10 minutes',
    schedule_interval='*/10 * * * *',  # Every 10 minutes
    start_date=datetime(2026, 1, 14),
    catchup=False,
    tags=['boreas', 'alerts', 'monitoring'],
)

check_alerts_task = PythonOperator(
    task_id='check_family_alerts',
    python_callable=check_family_alerts,
    dag=dag,
)

check_alerts_task
