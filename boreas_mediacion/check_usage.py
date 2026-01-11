import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'boreas_mediacion.settings')
django.setup()

from boreas_mediacion.models import WirelessLogic_SIM, WirelessLogic_Usage
from django.db.models import Sum, Count

print('=== RESUMEN WIRELESSLOGIC ===')
print(f'\nTotal SIMs: {WirelessLogic_SIM.objects.count()}')
print(f'Total Usage records: {WirelessLogic_Usage.objects.count()}')

stats = WirelessLogic_Usage.objects.aggregate(
    total_data=Sum('data_used_mb'),
    total_sms_sent=Sum('sms_sent'),
    total_sms_received=Sum('sms_received'),
    total_voice=Sum('voice_minutes')
)

print(f'\n=== TOTALES DE USO (mes actual) ===')
total_data = stats.get('total_data') or 0
total_sms_sent = stats.get('total_sms_sent') or 0
total_sms_received = stats.get('total_sms_received') or 0
total_voice = stats.get('total_voice') or 0

print(f'Total Data: {total_data:.2f} MB')
print(f'Total SMS enviados: {total_sms_sent}')
print(f'Total SMS recibidos: {total_sms_received}')
print(f'Total Voice: {total_voice:.2f} minutos')

sims_with_usage = WirelessLogic_Usage.objects.values('sim').distinct().count()
print(f'\nSIMs con datos de uso: {sims_with_usage} de {WirelessLogic_SIM.objects.count()}')

# Top 5 SIMs por uso de datos
print('\n=== TOP 5 SIMs por datos (mes actual) ===')
top_data = WirelessLogic_Usage.objects.select_related('sim').order_by('-data_used_mb')[:5]
for i, usage in enumerate(top_data, 1):
    print(f'{i}. {usage.sim.msisdn}: {usage.data_used_mb:.2f} MB')
