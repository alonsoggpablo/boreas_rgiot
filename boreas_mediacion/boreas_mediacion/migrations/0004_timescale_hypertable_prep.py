from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("boreas_mediacion", "0003_rename_reported_measure_device_feed_time_idx_boreas_medi_device__8bba22_idx"),
    ]

    operations = [
        migrations.RunSQL(
            sql=[
                "ALTER TABLE boreas_mediacion_reported_measure DROP CONSTRAINT IF EXISTS boreas_mediacion_reported_measure_pkey;",
                "CREATE UNIQUE INDEX IF NOT EXISTS reported_measure_id_report_time_uidx ON boreas_mediacion_reported_measure (id, report_time);",
            ],
            reverse_sql=[
                "DROP INDEX IF EXISTS reported_measure_id_report_time_uidx;",
                "ALTER TABLE boreas_mediacion_reported_measure ADD PRIMARY KEY (id);",
            ],
        ),
    ]
