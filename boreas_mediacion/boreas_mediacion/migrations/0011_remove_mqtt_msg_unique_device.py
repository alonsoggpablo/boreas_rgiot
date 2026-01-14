# Generated migration to remove unique constraint on mqtt_msg.device

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('boreas_mediacion', '0010_alert_updates_and_system_configuration'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mqtt_msg',
            name='device',
            field=models.JSONField(default=dict),
        ),
    ]
