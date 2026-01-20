"""
Airflow DAG to read DATADIS API every 60 minutes
"""
import sys
import os
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

# Add Django project to Python path
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'boreas_mediacion.settings')

def read_datadis_api():
    import django
    django.setup()
    from boreas_mediacion.datadis_service import DatadisService
    from boreas_mediacion.models import DatadisCredentials, DatadisSupply
    creds = DatadisCredentials.objects.filter(username="B27441401", password="Jl.295469!").first()
    if not creds:
        print("No valid DATADIS credentials found.")
        return
    service = DatadisService(credentials=creds)
    # Step 1: Get token explicitly
    token = service.authenticate()
    print(f"Obtained DATADIS token: {token[:30]}... (truncated)")
    # Step 2: Sync supplies to the database
    created, updated = service.sync_supplies()
    print(f"Supplies sync: {created} created, {updated} updated")
    return


default_args = {
    'owner': 'boreas',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'datadis_api_read',
    default_args=default_args,
    description='Read DATADIS API every 60 minutes',
    schedule_interval='0 * * * *',  # Every 60 minutes
    start_date=datetime(2026, 1, 18),
    catchup=False,
    tags=['datadis', 'api', 'monitoring'],
)

read_datadis_task = PythonOperator(
    task_id='read_datadis_api',
    python_callable=read_datadis_api,
    dag=dag,
)

read_datadis_task
