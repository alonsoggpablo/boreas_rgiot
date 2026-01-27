"""
Airflow DAG to read SIGFOX API every 60 minutes
"""
import sys
import os
import pendulum
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
    import pendulum
    # Set your credentials here
    usr = "rgiot"
    pwd = "rgiot"
    # Example device and data (replace with real logic if needed)
    device_id = "auto_sigfox_dag"
    data_hex = "102d0501f40f"
    ts = int(pendulum.now('Europe/Madrid').timestamp())
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

    # Save to DB directly (in addition to API call)
    try:
        from django.utils import timezone
        ts_dt = pendulum.from_timestamp(ts, tz='Europe/Madrid')
        fw = data_hex[0:1] if data_hex else None
        temp = hum = co2 = base = None
        try:
            temp = round((int(data_hex[2:6], 16) / 10) - 40, 2)
            hum = int(data_hex[6:8], 16)
            co2 = int(data_hex[8:12], 16)
            base = int(data_hex[12:14], 16)
        except Exception:
            pass
        device, _ = SigfoxDevice.objects.get_or_create(device_id=device_id)
        device.firmware = fw or device.firmware
        device.last_seen = ts_dt
        device.last_payload = payload
        device.last_co2 = co2
        device.last_temp = temp
        device.last_hum = hum
        device.last_base = base
        device.save()
        SigfoxReading.objects.create(
            device=device,
            timestamp=ts_dt,
            firmware=fw,
            co2=co2,
            temp=temp,
            hum=hum,
            base=base,
            raw_data=payload
        )
        print("SIGFOX API: Data saved to DB.")
    except Exception as e:
        print(f"SIGFOX API: Error saving to DB: {e}")
    print("SIGFOX API read and save completed.")


default_args = {
    'owner': 'boreas',
    'retries': 1,
    'retry_delay': pendulum.duration(minutes=5),
}

dag = DAG(
    'sigfox_api_read',
    default_args=default_args,
    description='Read SIGFOX API every 60 minutes',
    schedule_interval='0 * * * *',  # Every 60 minutes
    start_date=pendulum.datetime(2026, 1, 18, tz="Europe/Madrid"),
    catchup=False,
    tags=['sigfox', 'api', 'monitoring'],
)

read_sigfox_task = PythonOperator(
    task_id='read_sigfox_api',
    python_callable=read_sigfox_api,
    dag=dag,
)

read_sigfox_task
