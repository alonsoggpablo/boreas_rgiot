"""
Airflow DAG to run the Django management command populate_name_client_reported_measures
"""
from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'populate_name_client_reported_measures',
    default_args=default_args,
    description='Populate name and client fields in reported_measure from Gadget',
    schedule_interval=None,  # Set to desired schedule, e.g. '@daily'
    catchup=False,
)

run_populate = BashOperator(
    task_id='run_populate_name_client_reported_measures',
    bash_command='cd /app && python boreas_mediacion/manage.py populate_name_client_reported_measures',
    dag=dag,
)
