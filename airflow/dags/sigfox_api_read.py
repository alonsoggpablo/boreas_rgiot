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
    import requests
    import json
    django.setup()
    from boreas_mediacion.models import SigfoxDevice, SigfoxReading
    from django.utils import timezone
    # Set your credentials here
    usr = "rgiot"
    pwd = "rgiot"
    # Example device and data (replace with real logic if needed)
    device_id = "auto_sigfox_dag"
    data_hex = "102d0501f40f"
    ts = int(timezone.now().timestamp())
    url = "http://web:8000/api/sigfox"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Basic cmdpb3Q6cmdpb3Q="
    }
    payload = {"device": device_id, "data": data_hex, "timestamp": ts}
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=10)
        print(f"POST {url} status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error posting to Sigfox API: {e}")
    # Confirm data saved
    if SigfoxDevice.objects.filter(device_id=device_id).exists():
        device = SigfoxDevice.objects.get(device_id=device_id)
        readings = SigfoxReading.objects.filter(device=device)
        print(f"Readings count: {readings.count()}")
        for r in readings:
            print(r.timestamp, r.temp, r.hum, r.co2, r.base, r.raw_data)
    print("SIGFOX API read and save completed.")

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
