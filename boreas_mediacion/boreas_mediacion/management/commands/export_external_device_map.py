import json
import os
from datetime import datetime

from django.core.management.base import BaseCommand
from boreas_mediacion.models import Gadget


class Command(BaseCommand):
    help = "Export device mapping from local ExternalDeviceMapping table to a JSON file."

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            default="/app/media/external_devices_map.json",
            help="Output JSON file path",
        )

    def handle(self, *args, **options):
        output_path = options["output"]
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        device_map = {}

        # Export from Gadget table, indexed by uuid
        for gadget in Gadget.objects.all():
            uuid = getattr(gadget, "uuid", None)
            if not uuid:
                continue  # skip gadgets without uuid
            tipologia = (gadget.tipologia or '').lower()
            alias = (gadget.alias or '').lower()
            source = 'unknown'
            if 'nanoenvi' in tipologia or 'nanoenvi' in alias:
                source = 'nanoenvi'
            elif 'co2' in tipologia or 'co2' in alias:
                source = 'co2'
            elif 'router' in tipologia or 'router' in alias:
                source = 'routers'
            elif 'shelly' in tipologia or 'shelly' in alias:
                source = 'shellies'
            device_map[uuid] = {
                "name": gadget.alias or '',
                "client": gadget.cliente or '',
                "source": source,
            }

        payload = {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "count": len(device_map),
            "devices": device_map,
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

        self.stdout.write(self.style.SUCCESS(f"Exported {len(device_map)} devices from ExternalDeviceMapping to {output_path}"))

