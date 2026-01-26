"""
Airflow DAG to fetch AEMET API data for all active stations and store in Django models.
"""
import sys
import os
import requests
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

def fetch_aemet_data(**context):
    # Setup Django
    sys.path.insert(0, '/app')
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'boreas_mediacion.settings')
    import django
    django.setup()
    from boreas_mediacion.models import AemetStation, AemetData

    API_KEY = os.environ.get('AEMET_API_KEY', 'YOUR_API_KEY')
    BASE_URL = 'https://opendata.aemet.es/opendata/api/observacion/convencional/datos/estacion/{station_id}/?api_key={api_key}'

    for station in AemetStation.objects.filter(active=True):
        url = BASE_URL.format(station_id=station.station_id, api_key=API_KEY)
        try:
            resp = requests.get(url, timeout=30)
            if resp.status_code == 200:
                api_data = resp.json()
                datos_url = api_data.get('datos')
                if datos_url:
                    datos_resp = requests.get(datos_url, timeout=30)
                    if datos_resp.status_code == 200:
                        # The actual weather data is usually a JSON array or text
                        try:
                            datos_content = datos_resp.json()
                        except Exception:
                            datos_content = datos_resp.text
                        AemetData.objects.update_or_create(
                            station=station,
                            timestamp=datetime.utcnow(),
                            defaults={'data': datos_content}
                        )
                        print(f"Fetched and stored AEMET data for {station.station_id}")
                    else:
                        print(f"Failed to download datos for {station.station_id}: {datos_resp.status_code} {datos_resp.text}")
                else:
                    print(f"No 'datos' URL in API response for {station.station_id}: {api_data}")
            else:
                print(f"Failed for {station.station_id}: {resp.status_code} {resp.text}")
        except Exception as e:
            print(f"Error fetching {station.station_id}: {e}")

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'aemet_api_fetch',
    default_args=default_args,
    description='Fetch AEMET API data for all active stations',
    schedule_interval='0 * * * *',
    catchup=False,
    tags=['aemet', 'api', 'weather'],
)

fetch_task = PythonOperator(
    task_id='fetch_aemet_data',
    python_callable=fetch_aemet_data,
    dag=dag,
)
