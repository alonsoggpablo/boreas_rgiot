"""
Airflow DAG to read WirelessLogic API every 60 minutes
"""
import sys
import os
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

# Add Django project to Python path
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'boreas_mediacion.settings')

def read_wireless_api():
    import django
    django.setup()
    from boreas_mediacion.wirelesslogic_service import WirelessLogicService
    service = WirelessLogicService()
    # Implement the actual API read logic here
    created, updated = service.sync_all_sims()
    print(f"WirelessLogic SIMs - created: {created}, updated: {updated}")
    usage_count = service.sync_sim_usage()
    print(f"WirelessLogic usage records created/updated: {usage_count}")
    print("WirelessLogic API read and DB save completed.")

default_args = {
    'owner': 'boreas',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'wireless_api_read',
    default_args=default_args,
    description='Read WirelessLogic API every 60 minutes',
    schedule_interval='0 * * * *',  # Every 60 minutes
    start_date=datetime(2026, 1, 18),
    catchup=False,
    tags=['wirelesslogic', 'api', 'monitoring'],
)

read_wireless_task = PythonOperator(
    task_id='read_wireless_api',
    python_callable=read_wireless_api,
    dag=dag,
)

read_wireless_task
