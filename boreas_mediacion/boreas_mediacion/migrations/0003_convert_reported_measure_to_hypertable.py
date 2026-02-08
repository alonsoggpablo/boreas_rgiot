from django.db import migrations


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ("boreas_mediacion", "0002_add_device_id_report_time_index"),
    ]

    operations = [
        migrations.RunSQL(
            sql=(
                "ALTER TABLE boreas_mediacion_reported_measure "
                "DROP CONSTRAINT IF EXISTS boreas_mediacion_reported_measure_pkey;"
            ),
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql=(
                "CREATE INDEX IF NOT EXISTS reported_meas_id_idx "
                "ON boreas_mediacion_reported_measure (id);"
            ),
            reverse_sql=(
                "DROP INDEX IF EXISTS reported_meas_id_idx;"
            ),
        ),
        migrations.RunSQL(
            sql=(
                "SELECT create_hypertable("
                "'boreas_mediacion_reported_measure', "
                "'report_time', "
                "if_not_exists => TRUE, "
                "migrate_data => TRUE"
                ");"
            ),
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
