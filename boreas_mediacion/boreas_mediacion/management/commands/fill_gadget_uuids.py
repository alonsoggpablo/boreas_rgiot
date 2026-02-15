import sys
from django.core.management.base import BaseCommand
from boreas_mediacion.models import Gadget
from boreas_mediacion.external_device_models import ExternalDevice

class Command(BaseCommand):
    help = "Fill missing Gadget.uuid and uuid_ip fields from ExternalDevice, matching by device_id."

    def handle(self, *args, **options):
        updated = 0
        missing = 0
        for gadget in Gadget.objects.all():
            if not gadget.uuid or not gadget.uuid_ip:
                ext = ExternalDevice.objects.filter(device_id=gadget.device_id).first()
                if ext:
                    changed = False
                    if not gadget.uuid and ext.uuid:
                        gadget.uuid = ext.uuid
                        changed = True
                    if not gadget.uuid_ip and ext.uuid_ip:
                        gadget.uuid_ip = ext.uuid_ip
                        changed = True
                    if changed:
                        gadget.save(update_fields=[f for f in ["uuid", "uuid_ip"] if getattr(gadget, f)])
                        updated += 1
                else:
                    missing += 1
        self.stdout.write(self.style.SUCCESS(f"Updated {updated} Gadget records. {missing} had no matching ExternalDevice."))