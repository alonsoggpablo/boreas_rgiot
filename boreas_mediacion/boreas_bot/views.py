from .models import DevicesROUTERS, DevicesNANOENVI, DevicesCO2

# Custom view to display the first 100 rows of each devices* model from the external DB
def devices_external_list(request):
    name_filter = request.GET.get('name', '').strip()
    routers = DevicesROUTERS.objects.all()
    nanoenvi = DevicesNANOENVI.objects.all()
    co2 = DevicesCO2.objects.all()
    if name_filter:
        routers = routers.filter(name__icontains=name_filter)
        nanoenvi = nanoenvi.filter(name__icontains=name_filter)
        co2 = co2.filter(name__icontains=name_filter)
    router_fields = [f.name for f in DevicesROUTERS._meta.fields]
    nanoenvi_fields = [f.name for f in DevicesNANOENVI._meta.fields]
    co2_fields = [f.name for f in DevicesCO2._meta.fields]
    return render(request, 'boreas_bot/devices_external_list.html', {
        'routers': routers,
        'nanoenvi': nanoenvi,
        'co2': co2,
        'router_fields': router_fields,
        'nanoenvi_fields': nanoenvi_fields,
        'co2_fields': co2_fields,
        'name_filter': name_filter,
    })
# boreas_bot/views.py
from django.shortcuts import render
from django.http import HttpResponse
from django.db import connections

def list_devices_tables(request):
    db_conn = connections['default']
    with db_conn.cursor() as cursor:
        cursor.execute("SELECT tablename FROM pg_catalog.pg_tables WHERE tablename ILIKE 'devices%'")
        tables = [row[0] for row in cursor.fetchall()]
    return render(request, 'boreas_bot/devices_tables.html', {'tables': tables})
