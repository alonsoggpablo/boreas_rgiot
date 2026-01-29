import os
import django

def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'boreas_mediacion.settings')
    django.setup()
    from boreas_mediacion.models import reported_measure, MQTT_device_family

    count = 0
    for rm in reported_measure.objects.all():
        if rm.feed:
            family_name = rm.feed.split('/')[0]
            family = MQTT_device_family.objects.filter(name=family_name).first()
            if family:
                rm.device_family_id = family
                rm.save(update_fields=['device_family_id'])
                count += 1
    print(f"Updated {count} reported_measure records with device_family_id.")

if __name__ == "__main__":
    main()
