import json
import os
from datetime import datetime

from django.core.management.base import BaseCommand
from boreas_mediacion.models import ExternalDeviceMapping


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

        # Export from local ExternalDeviceMapping table
        for device in ExternalDeviceMapping.objects.all():
            device_type = device.metadata.get('device_type', 'unknown')
            
            # Map device_type to source
            source = 'unknown'
            if 'nanoenvi' in device_type.lower():
                source = 'nanoenvi'
            elif 'co2' in device_type.lower():
                source = 'co2'
            elif 'router' in device_type.lower():
                source = 'routers'
            elif 'shelly' in device_type.lower():
                source = 'shellies'
            
            device_map[str(device.external_device_id)] = {
                "name": device.external_alias,
                "client": device.client_name,
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

