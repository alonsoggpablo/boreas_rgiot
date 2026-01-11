#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'boreas_mediacion.settings')
django.setup()

from boreas_mediacion.models import WirelessLogic_SIM
from django.db.models import Count

print('=== Resumen de SIMs ===')
print(f'Total SIMs: {WirelessLogic_SIM.objects.count()}')

print('\nSIMs por estado:')
for status in WirelessLogic_SIM.objects.values('status').annotate(count=Count('id')).order_by('-count')[:10]:
    print(f'  {status["status"] or "None"}: {status["count"]}')

print('\nTarifas más comunes:')
for tariff in WirelessLogic_SIM.objects.exclude(tariff_name__isnull=True).values('tariff_name').annotate(count=Count('id')).order_by('-count')[:5]:
    print(f'  {tariff["tariff_name"]}: {tariff["count"]}')

print('\nRedes (MNO):')
for net in WirelessLogic_SIM.objects.exclude(network__isnull=True).values('network').annotate(count=Count('id')).order_by('-count')[:5]:
    print(f'  {net["network"]}: {net["count"]}')

print('\nMuestra de 3 SIMs:')
for sim in WirelessLogic_SIM.objects.all()[:3]:
    print(f'\n  ICCID: {sim.iccid}')
    print(f'  MSISDN: {sim.msisdn}')
    print(f'  Status: {sim.status}')
    print(f'  Tariff: {sim.tariff_name}')
    print(f'  Network: {sim.network}')
