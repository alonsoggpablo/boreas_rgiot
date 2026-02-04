from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('boreas_mediacion', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='mqtt_topic',
            name='monitored',
            field=models.BooleanField(default=False),
        ),
    ]
