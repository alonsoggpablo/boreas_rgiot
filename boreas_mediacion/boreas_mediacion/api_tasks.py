from celery import shared_task
import pendulum
import os
import sys

@shared_task
def read_sigfox_api():
    import django
    import requests
    import json
    django.setup()
    from boreas_mediacion.models import SigfoxDevice, SigfoxReading
    # Set your credentials here
    usr = "rgiot"
    pwd = "rgiot"
    device_id = "auto_sigfox_dag"
    data_hex = "102d0501f40f"
    ts = int(pendulum.now('Europe/Madrid').timestamp())
    url = "http://web:8000/api/sigfox"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Basic cmdpb3Q6cmdpb3Q="
    }
    payload = {"device": device_id, "data": data_hex, "timestamp": ts}
    post_status = None
    post_response = None
    post_error = None
    db_error = None
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=10)
        post_status = response.status_code
        post_response = response.text
    except Exception as e:
        post_error = str(e)
    try:
        ts_dt = pendulum.from_timestamp(ts, tz='Europe/Madrid')
        fw = data_hex[0:1] if data_hex else None
        temp = hum = co2 = base = None
        try:
            temp = round((int(data_hex[2:6], 16) / 10) - 40, 2)
            hum = int(data_hex[6:8], 16)
            co2 = int(data_hex[8:12], 16)
            base = int(data_hex[12:14], 16)
        except Exception:
            pass
        device, _ = SigfoxDevice.objects.get_or_create(device_id=device_id)
        device.firmware = fw or device.firmware
        device.last_seen = ts_dt
        device.last_payload = payload
        device.last_co2 = co2
        device.last_temp = temp
        device.last_hum = hum
        device.last_base = base
        device.save()
        SigfoxReading.objects.create(
            device=device,
            timestamp=ts_dt,
            firmware=fw,
            co2=co2,
            temp=temp,
            hum=hum,
            base=base,
            raw_data=payload
        )
    except Exception as e:
        db_error = str(e)
    result = {
        "post_status": post_status,
        "post_error": post_error,
        "db_error": db_error,
        "post_response": post_response
    }
    return result

@shared_task
def read_datadis_api():
    import django
    django.setup()
    from boreas_mediacion.datadis_service import DatadisService
    from boreas_mediacion.models import DatadisCredentials, DatadisSupply
    creds = DatadisCredentials.objects.filter(username="B27441401", password="Jl.295469!").first()
    if not creds:
        return "No valid DATADIS credentials found."
    service = DatadisService(credentials=creds)
    token = service.authenticate()
    created, updated = service.sync_supplies()
    return f"Supplies sync: {created} created, {updated} updated, token: {token[:10]}..."

@shared_task
def read_wireless_api():
    import django
    django.setup()
    from boreas_mediacion.wirelesslogic_service import WirelessLogicService
    service = WirelessLogicService()
    created, updated = service.sync_all_sims()
    usage_count = service.sync_sim_usage()
    return f"WirelessLogic SIMs - created: {created}, updated: {updated}, usage records: {usage_count}"
