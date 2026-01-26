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
    schedule_interval='*/30 * * * *',  # Every 30 minutes
    catchup=False,
    tags=['boreas', 'alerts', 'monitoring'],
)



# New function to check all active alert rules
def check_all_active_alerts():
    """
    Python function to check all active alert rules (disk, device, families_last_readings, ram, etc.)
    """
    import os
    import sys
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'boreas_mediacion.settings')
    sys.path.insert(0, '/app')
    django.setup()

    from boreas_mediacion.alert_service import AlertService
    from boreas_mediacion.models import Alert
    from django.utils import timezone

    # Resolve all active alerts at the start of each DAG run
    resolved_count = Alert.objects.filter(status='active').update(status='resolved', resolved_at=timezone.now())
    print(f"[DAG INIT] Resolved {resolved_count} active alerts at start of DAG run.")

    print("\n==============================")
    print("Checking ALL active alert rules")
    print("==============================\n")
    service = AlertService()
    alerts = service.check_active_rules()
    print(f"Triggered {len(alerts)} alert(s)")


# Task: Check all active alerts (runs at 02:00, 09:00, 10:00)
check_all_alerts = PythonOperator(
    task_id='check_all_active_alerts',
    python_callable=check_all_active_alerts,
    dag=dag,
)
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
    schedule_interval='*/30 * * * *',  # Every 30 minutes
    catchup=False,
    tags=['boreas', 'alerts', 'monitoring'],
)



# New function to check all active alert rules
def check_all_active_alerts():
    """
    Python function to check all active alert rules (disk, device, families_last_readings, ram, etc.)
    """
    import os
    import sys
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'boreas_mediacion.settings')
    sys.path.insert(0, '/app')
    django.setup()

    from boreas_mediacion.alert_service import AlertService
    from boreas_mediacion.models import Alert
    from django.utils import timezone

    # Resolve all active alerts at the start of each DAG run
    resolved_count = Alert.objects.filter(status='active').update(status='resolved', resolved_at=timezone.now())
    print(f"[DAG INIT] Resolved {resolved_count} active alerts at start of DAG run.")

    print("\n==============================")
    print("Checking ALL active alert rules")
    print("==============================\n")
    service = AlertService()
    alerts = service.check_active_rules()
    print(f"Triggered {len(alerts)} alert(s)")



# Task: Check all active alerts (runs at 02:00, 09:00, 10:00)
check_all_alerts = PythonOperator(
    task_id='check_all_active_alerts',
    python_callable=check_all_active_alerts,
    dag=dag,
)
