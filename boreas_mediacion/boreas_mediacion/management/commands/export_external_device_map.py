import json
import os
from datetime import datetime

from django.core.management.base import BaseCommand
from django.db import connections
from psycopg2 import sql

from boreas_bot.models import DevicesNANOENVI, DevicesCO2, DevicesROUTERS


class Command(BaseCommand):
    help = "Export uuid/name/client mapping from external devices tables to a JSON file."

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

        # NANOENVI
        for d in DevicesNANOENVI.objects.all():
            device_map[str(d.uuid)] = {
                "name": d.name,
                "client": d.client,
                "source": "nanoenvi",
            }

        # CO2
        for d in DevicesCO2.objects.all():
            device_map[str(d.id)] = {
                "name": d.name,
                "client": d.client,
                "source": "co2",
            }

        # ROUTERS
        for d in DevicesROUTERS.objects.all():
            device_map[str(d.id)] = {
                "name": d.name,
                "client": None,
                "source": "routers",
            }

        # SHELLIES (raw table if present in external DB)
        shellies_table = self._find_shellies_table()
        if shellies_table:
            self._load_shellies_table(shellies_table, device_map)

        payload = {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "count": len(device_map),
            "devices": device_map,
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

        self.stdout.write(self.style.SUCCESS(f"Exported {len(device_map)} devices to {output_path}"))

    def _find_shellies_table(self):
        # Prefer explicit devicesSHELLIES table name
        try:
            with connections["external"].cursor() as cursor:
                cursor.execute(
                    """
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                      AND table_name IN ('devicesSHELLIES', 'devicesshellies', 'devices_shellies')
                    """
                )
                row = cursor.fetchone()
                if row:
                    return row[0]

                cursor.execute(
                    """
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                      AND table_name ILIKE 'devices%'
                    ORDER BY table_name
                    """
                )
                tables = [r[0] for r in cursor.fetchall()]
        except Exception:
            return None

        for name in tables:
            if "shellies" in name.lower():
                return name
        return None

    def _load_shellies_table(self, table_name, device_map):
        # Try to map common column names: uuid/id, name, client
        with connections["external"].cursor() as cursor:
            cursor.execute(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = %s
                """,
                [table_name],
            )
            columns = [row[0] for row in cursor.fetchall()]

            id_col = "uuid" if "uuid" in columns else ("id" if "id" in columns else None)
            name_col = "name" if "name" in columns else None
            client_col = "client" if "client" in columns else None

            if not id_col:
                return

            select_cols = [id_col]
            if name_col:
                select_cols.append(name_col)
            if client_col:
                select_cols.append(client_col)

            query = sql.SQL("SELECT {fields} FROM {table}").format(
                fields=sql.SQL(', ').join(sql.Identifier(c) for c in select_cols),
                table=sql.Identifier(table_name),
            )
            try:
                cursor.execute(query)
                rows = cursor.fetchall()
            except Exception:
                return

        for row in rows:
            device_id = str(row[0])
            name = row[select_cols.index(name_col)] if name_col else None
            client = row[select_cols.index(client_col)] if client_col else None
            device_map[device_id] = {
                "name": name,
                "client": client,
                "source": "shellies",
            }
