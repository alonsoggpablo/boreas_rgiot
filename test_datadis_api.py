
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'boreas_mediacion')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'boreas_mediacion.settings')
import django
django.setup()

from boreas_mediacion.datadis_service import DatadisService

service = DatadisService()
print('Authenticating with DATADIS...')
token = service.authenticate()
print(f'Token: {token}')

print('Syncing supply points...')
supplies = service.sync_supplies()
print(f'Supplies sync result: {supplies}')

print('Syncing consumption and max power for all supplies...')
summary = service.sync_all_supplies_consumption()
print(f'Consumption/max power sync summary: {summary}')
