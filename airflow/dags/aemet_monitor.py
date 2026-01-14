"""
Airflow DAG to monitor AEMET weather data arrivals
Runs every 5 minutes and sends email notifications when new data is detected
"""
import sys
import os

# Add Django project to Python path FIRST, before any imports
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'boreas_mediacion.settings')

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import subprocess


def check_aemet_data(**context):
    """
    Execute Django management command to check for AEMET data
    """
    import os
    import django
    
    # Setup Django to access database
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'boreas_mediacion.settings')
    django.setup()
    
    from boreas_mediacion.models import SystemConfiguration
    
    # Get email recipient from database configuration
    recipient = SystemConfiguration.get_value('aemet_alert_email', 'alonsogpablo@rggestionyenergia.com')
    
    try:
        # Run the Django management command
        result = subprocess.run(
            [
                'python',
                '/app/manage.py',
                'check_aemet_data',
                '--minutes', '5',
                '--recipient', recipient
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


def get_airflow_email():
    """Get Airflow failure notification email from database"""
    import os
    import django
    
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'boreas_mediacion.settings')
    django.setup()
    
    from boreas_mediacion.models import SystemConfiguration
    
    email = SystemConfiguration.get_value('airflow_failure_email', 'alonsogpablo@rggestionyenergia.com')
    return [email]

# Default arguments for the DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email': get_airflow_email(),
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
