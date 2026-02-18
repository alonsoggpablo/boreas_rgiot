import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'boreas_mediacion.settings')

app = Celery('boreas_mediacion')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
