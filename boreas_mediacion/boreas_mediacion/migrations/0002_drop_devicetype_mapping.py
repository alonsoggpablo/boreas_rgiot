from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('boreas_mediacion', '0001_initial'),
    ]
    operations = [
        migrations.RunSQL(
            sql='DROP TABLE IF EXISTS boreas_mediacion_device_type_mapping;',
            reverse_sql='',
        ),
    ]
