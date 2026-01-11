from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('boreas_mediacion', '0006_datadiscredentials_datadissupply_datadismaxpower_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='AlertRule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('rule_type', models.CharField(choices=[('disk_space', 'Disk Space'), ('device_connection', 'Device Connection'), ('aemet_data', 'AEMET Weather Data')], max_length=50)),
                ('check_interval_minutes', models.IntegerField(default=5)),
                ('enabled', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Alert',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('triggered_at', models.DateTimeField(auto_now_add=True)),
                ('message', models.TextField()),
                ('resolved', models.BooleanField(default=False)),
                ('resolved_at', models.DateTimeField(blank=True, null=True)),
                ('rule', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='boreas_mediacion.alertrule')),
            ],
            options={
                'ordering': ['-triggered_at'],
            },
        ),
        migrations.CreateModel(
            name='AlertNotification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('recipient_email', models.EmailField(max_length=254)),
                ('sent_at', models.DateTimeField(auto_now_add=True)),
                ('alert', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='boreas_mediacion.alert')),
            ],
        ),
    ]
