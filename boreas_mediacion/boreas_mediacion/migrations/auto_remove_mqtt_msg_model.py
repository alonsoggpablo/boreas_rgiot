from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ("boreas_mediacion", "auto_remove_mqtt_msg_model"),
    ]

    operations = [
        migrations.DeleteModel(
            name="mqtt_msg",
        ),
    ]
