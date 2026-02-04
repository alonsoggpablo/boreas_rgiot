"""
Airflow DAG to export external devices map to JSON every hour
"""
import sys
import os
import pendulum
from airflow import DAG
from airflow.operators.python import PythonOperator

# Add Django project to Python path
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'boreas_mediacion.settings')


def export_device_map():
    import django
    django.setup()
    from django.core.management import call_command

    call_command(
        'export_external_device_map',
        output='/app/media/external_devices_map.json',
    )


default_args = {
    'owner': 'boreas',
    'retries': 1,
    'retry_delay': pendulum.duration(minutes=5),
}

dag = DAG(
    'export_external_device_map',
    default_args=default_args,
    description='Export external devices map every hour',
    schedule_interval='0 * * * *',
    start_date=pendulum.datetime(2026, 2, 4, tz="Europe/Madrid"),
    catchup=False,
    tags=['devices', 'external', 'export'],
)

export_task = PythonOperator(
    task_id='export_external_device_map',
    python_callable=export_device_map,
    dag=dag,
)

export_task
