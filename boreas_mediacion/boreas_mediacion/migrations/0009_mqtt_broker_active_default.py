from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('boreas_mediacion', '0008_reported_measure_unique_constraint'),
    ]

    operations = [
        # Update default value for active field
        migrations.AlterField(
            model_name='mqtt_broker',
            name='active',
            field=models.BooleanField(default=True),
        ),
        # Activate all existing brokers
        migrations.RunSQL(
            sql="UPDATE boreas_mediacion_mqtt_broker SET active = TRUE;",
            reverse_sql="UPDATE boreas_mediacion_mqtt_broker SET active = FALSE;",
        ),
    ]
