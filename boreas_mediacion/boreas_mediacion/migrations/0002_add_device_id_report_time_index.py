from django.db import migrations


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ("boreas_mediacion", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(
            sql=(
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS "
                "reported_meas_device_id_report_time_idx "
                "ON boreas_mediacion_reported_measure (device_id, report_time)"
            ),
            reverse_sql=(
                "DROP INDEX CONCURRENTLY IF EXISTS "
                "reported_meas_device_id_report_time_idx"
            ),
        ),
    ]
