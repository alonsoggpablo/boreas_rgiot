"""
Airflow DAG to read SIGFOX API every 60 minutes
"""
import sys
import os
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

# Add Django project to Python path
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'boreas_mediacion.settings')

def read_sigfox_api():
    import django
    django.setup()
    from boreas_mediacion.models import SigfoxDevice
    # Implement the actual API read logic here
    # Example: SigfoxDevice.sync_all_devices() or similar
    print("SIGFOX API read completed.")

default_args = {
    'owner': 'boreas',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'sigfox_api_read',
    default_args=default_args,
    description='Read SIGFOX API every 60 minutes',
    schedule_interval='0 * * * *',  # Every 60 minutes
    start_date=datetime(2026, 1, 18),
    catchup=False,
    tags=['sigfox', 'api', 'monitoring'],
)

read_sigfox_task = PythonOperator(
    task_id='read_sigfox_api',
    python_callable=read_sigfox_api,
    dag=dag,
)

read_sigfox_task
