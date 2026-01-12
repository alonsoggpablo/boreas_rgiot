"""
Airflow DAG to monitor AEMET weather data arrivals
Runs every 5 minutes and sends email notifications when new data is detected
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import subprocess
import sys
import os


# Add Django project to Python path
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'boreas_mediacion.settings')


def check_aemet_data(**context):
    """
    Execute Django management command to check for AEMET data
    """
    try:
        # Run the Django management command
        result = subprocess.run(
            [
                'python',
                '/app/manage.py',
                'check_aemet_data',
                '--minutes', '5',
                '--recipient', 'alonsogpablo@gestionyenergia.com'
            ],
            cwd='/app',
            capture_output=True,
            text=True,
            timeout=60
        )
        
        # Log output
        print("=== STDOUT ===")
        print(result.stdout)
        
        if result.stderr:
            print("=== STDERR ===")
            print(result.stderr)
        
        # Check if command succeeded
        if result.returncode != 0:
            raise Exception(f"Command failed with return code {result.returncode}")
        
        print(f"✅ AEMET data check completed successfully")
        return result.stdout
        
    except subprocess.TimeoutExpired:
        raise Exception("AEMET data check timed out after 60 seconds")
    except Exception as e:
        raise Exception(f"Error checking AEMET data: {str(e)}")


# Default arguments for the DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email': ['alonsogpablo@gestionyenergia.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
}

# Define the DAG
dag = DAG(
    'aemet_data_monitor',
    default_args=default_args,
    description='Monitor AEMET weather data arrivals every 5 minutes',
    schedule_interval='*/5 * * * *',  # Every 5 minutes
    start_date=datetime(2026, 1, 11),
    catchup=False,
    tags=['aemet', 'weather', 'monitoring', 'test'],
)

# Define the task
check_aemet_task = PythonOperator(
    task_id='check_aemet_data',
    python_callable=check_aemet_data,
    dag=dag,
    provide_context=True,
)

# Task sequence (only one task in this simple DAG)
check_aemet_task
