#!/bin/bash
# Reload Airflow webserver and scheduler using both docker-compose files

echo "Restarting Airflow webserver and scheduler..."
docker compose -f docker-compose.yml -f docker-compose.airflow.yml restart airflow-webserver airflow-scheduler

echo "Done. Check Airflow UI and logs for DAG status."
