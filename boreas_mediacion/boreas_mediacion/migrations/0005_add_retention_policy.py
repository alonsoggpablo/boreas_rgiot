from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("boreas_mediacion", "0004_alter_reported_measure_options"),
    ]

    operations = [
        migrations.RunSQL(
            sql=(
                "SELECT add_retention_policy("
                "'boreas_mediacion_reported_measure', "
                "INTERVAL '24 hours', "
                "if_not_exists => TRUE"
                ");"
            ),
            reverse_sql=(
                "SELECT remove_retention_policy("
                "'boreas_mediacion_reported_measure', "
                "if_exists => TRUE"
                ");"
            ),
        ),
    ]
