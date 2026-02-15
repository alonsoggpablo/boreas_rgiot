"""
Airflow DAG to fetch AEMET API data for all active stations and store in Django models.
"""
import sys
import os
import requests
import pendulum
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

    success_count = 0
    error_count = 0
    errors = []

    for station in AemetStation.objects.filter(station_id="1207U", active=True):
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
                            timestamp=pendulum.now('Europe/Madrid'),
                            defaults={'data': datos_content}
                        )
                        print(f"Fetched and stored AEMET data for {station.station_id}")
                        success_count += 1
                    else:
                        error_msg = f"Failed to download datos for {station.station_id}: {datos_resp.status_code} {datos_resp.text}"
                        print(error_msg)
                        errors.append(error_msg)
                        error_count += 1
                else:
                    error_msg = f"No 'datos' URL in API response for {station.station_id}: {api_data}"
                    print(error_msg)
                    errors.append(error_msg)
                    error_count += 1
            elif resp.status_code == 401:
                # 401 errors are critical - API key revoked or expired
                error_msg = f"API KEY ERROR for {station.station_id}: {resp.status_code} {resp.text}"
                print(error_msg)
                errors.append(error_msg)
                error_count += 1
            else:
                error_msg = f"Failed for {station.station_id}: {resp.status_code} {resp.text}"
                print(error_msg)
                errors.append(error_msg)
                error_count += 1
        except Exception as e:
            error_msg = f"Error fetching {station.station_id}: {e}"
            print(error_msg)
            errors.append(error_msg)
            error_count += 1
    
    # Raise exception if ALL stations failed (likely API key issue)
    if error_count > 0 and success_count == 0:
        raise Exception(f"AEMET API fetch failed for all {error_count} stations. Errors: {'; '.join(errors[:3])}")
    elif error_count > 0:
        print(f"⚠️  Warning: {error_count}/{error_count + success_count} stations failed")
    
    print(f"✅ Successfully fetched data from {success_count} stations")


default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': pendulum.datetime(2024, 1, 1, tz="Europe/Madrid"),
    'retries': 1,
    'retry_delay': pendulum.duration(minutes=5),
}

dag = DAG(
    'aemet_api_fetch',
    default_args=default_args,
    description='Fetch AEMET API data for all active stations',
    schedule='0 * * * *',
    catchup=False,
    tags=['aemet', 'api', 'weather'],
)

fetch_task = PythonOperator(
    task_id='fetch_aemet_data',
    python_callable=fetch_aemet_data,
    dag=dag,
)
