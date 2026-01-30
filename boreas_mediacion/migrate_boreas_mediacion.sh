#!/bin/bash
set -e

docker-compose exec web python3 /app/boreas_mediacion/manage.py migrate boreas_mediacion

docker-compose exec web python3 /app/boreas_mediacion/manage.py makemigrations
docker-compose exec web python3 /app/boreas_mediacion/manage.py migrate
