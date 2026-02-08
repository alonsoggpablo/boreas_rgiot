"""
Airflow DAG to dump reported_measure records to Parquet files.
Runs daily at 2 AM, archives records older than 24 hours.
"""
import sys
import os
import importlib.util
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import pendulum

def dump_reported_measures(**context):
    """Execute the Parquet dump script."""
    sys.path.insert(0, '/app/boreas_mediacion')
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'boreas_mediacion.settings')
    
    # Import the actual module from boreas_mediacion package
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "dump_module", 
        "/app/boreas_mediacion/dump_reported_measures_to_parquet.py"
    )
    dump_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(dump_module)
    
    # Execute the dump function
    dump_module.dump_to_parquet()
    print("✓ Parquet dump completed successfully")

# DAG Configuration
default_args = {
    'owner': 'boreas',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'dump_reported_measures_to_parquet',
    default_args=default_args,
    description='Daily dump of reported_measure records older than 24 hours to Parquet',
    schedule_interval='0 2 * * *',  # 2 AM daily
    start_date=pendulum.parse('2026-02-06', strict=False),
    catchup=False,
    tags=['data-archive', 'reported-measures'],
) as dag:
    
    dump_task = PythonOperator(
        task_id='dump_to_parquet',
        python_callable=dump_reported_measures,
        provide_context=True,
    )
    
    dump_task
