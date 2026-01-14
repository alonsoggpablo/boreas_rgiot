from django.db import migrations, models
from django.utils import timezone


class Migration(migrations.Migration):

    dependencies = [
        ('boreas_mediacion', '0009_mqtt_broker_active_default'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            # Database operations only create the missing table; all other fields already exist in the DB.
            database_operations=[
                migrations.CreateModel(
                    name='SystemConfiguration',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('config_type', models.CharField(choices=[('email', 'Email Configuration'), ('alert', 'Alert Configuration'), ('airflow', 'Airflow Configuration'), ('general', 'General Configuration')], default='general', max_length=50)),
                        ('key', models.CharField(db_index=True, default='', help_text='Clave de configuración (ej: airflow_alert_email)', max_length=100, unique=True)),
                        ('value', models.TextField(default='', help_text='Valor de la configuración')),
                        ('description', models.TextField(blank=True, default='', help_text='Descripción de la configuración', null=True)),
                        ('active', models.BooleanField(default=True)),
                        ('created_at', models.DateTimeField(auto_now_add=True)),
                        ('updated_at', models.DateTimeField(auto_now=True)),
                    ],
                    options={
                        'ordering': ['config_type', 'key'],
                        'verbose_name': 'System Configuration',
                        'verbose_name_plural': 'System Configurations',
                    },
                ),
            ],
            # State operations declare the full model state without reapplying columns already present.
            state_operations=[
                # AlertRule updates
                migrations.AddField(
                    model_name='alertrule',
                    name='active',
                    field=models.BooleanField(default=True),
                ),
                migrations.AddField(
                    model_name='alertrule',
                    name='config',
                    field=models.JSONField(default=dict, help_text='Configuración específica de la regla'),
                ),
                migrations.AddField(
                    model_name='alertrule',
                    name='description',
                    field=models.TextField(blank=True, default='', help_text='Descripción de la regla', null=True),
                ),
                migrations.AddField(
                    model_name='alertrule',
                    name='last_check',
                    field=models.DateTimeField(blank=True, null=True),
                ),
                migrations.AddField(
                    model_name='alertrule',
                    name='notification_recipients',
                    field=models.TextField(default='', help_text='Destinatarios separados por comas'),
                ),
                migrations.AddField(
                    model_name='alertrule',
                    name='notification_subject',
                    field=models.CharField(blank=True, default='', max_length=500, null=True),
                ),
                migrations.AddField(
                    model_name='alertrule',
                    name='notification_type',
                    field=models.CharField(choices=[('email', 'Email'), ('mqtt', 'MQTT')], default='email', max_length=20),
                ),
                migrations.AddField(
                    model_name='alertrule',
                    name='threshold',
                    field=models.IntegerField(blank=True, help_text='Umbral para activar alerta (ej: 89 para 89% disco)', null=True),
                ),
                migrations.AlterField(
                    model_name='alertrule',
                    name='check_interval_minutes',
                    field=models.IntegerField(default=60, help_text='Intervalo de verificación en minutos'),
                ),
                migrations.AlterField(
                    model_name='alertrule',
                    name='name',
                    field=models.CharField(default='', help_text='Nombre de la regla de alerta', max_length=200),
                ),
                migrations.AlterField(
                    model_name='alertrule',
                    name='rule_type',
                    field=models.CharField(choices=[('disk_space', 'Disk Space'), ('device_connection', 'Device Connection'), ('aemet_data', 'AEMET Weather Data'), ('custom', 'Custom Check')], db_index=True, default='custom', max_length=50),
                ),
                migrations.AlterModelOptions(
                    name='alertrule',
                    options={'ordering': ['name'], 'verbose_name': 'Alert Rule', 'verbose_name_plural': 'Alert Rules'},
                ),

                # Alert updates
                migrations.AddField(
                    model_name='alert',
                    name='acknowledged_at',
                    field=models.DateTimeField(blank=True, null=True),
                ),
                migrations.AddField(
                    model_name='alert',
                    name='alert_type',
                    field=models.CharField(blank=True, db_index=True, default='general', max_length=50),
                ),
                migrations.AddField(
                    model_name='alert',
                    name='details',
                    field=models.JSONField(default=dict, help_text='Detalles adicionales de la alerta'),
                ),
                migrations.AddField(
                    model_name='alert',
                    name='severity',
                    field=models.CharField(choices=[('info', 'Info'), ('warning', 'Warning'), ('error', 'Error'), ('critical', 'Critical')], default='warning', max_length=20),
                ),
                migrations.AddField(
                    model_name='alert',
                    name='status',
                    field=models.CharField(choices=[('active', 'Active'), ('acknowledged', 'Acknowledged'), ('resolved', 'Resolved')], db_index=True, default='active', max_length=20),
                ),
                migrations.AlterField(
                    model_name='alert',
                    name='message',
                    field=models.TextField(default=''),
                ),
                migrations.AlterField(
                    model_name='alert',
                    name='resolved_at',
                    field=models.DateTimeField(blank=True, null=True),
                ),
                migrations.AlterField(
                    model_name='alert',
                    name='rule',
                    field=models.ForeignKey(blank=True, null=True, on_delete=models.CASCADE, related_name='alerts', to='boreas_mediacion.alertrule'),
                ),
                migrations.AlterField(
                    model_name='alert',
                    name='triggered_at',
                    field=models.DateTimeField(auto_now_add=True, db_index=True),
                ),
                migrations.AlterModelOptions(
                    name='alert',
                    options={'ordering': ['-triggered_at'], 'verbose_name': 'Alert', 'verbose_name_plural': 'Alerts'},
                ),

                # AlertNotification updates
                migrations.AddField(
                    model_name='alertnotification',
                    name='created_at',
                    field=models.DateTimeField(default=timezone.now),
                ),
                migrations.AddField(
                    model_name='alertnotification',
                    name='error_message',
                    field=models.TextField(blank=True, null=True),
                ),
                migrations.AddField(
                    model_name='alertnotification',
                    name='message',
                    field=models.TextField(default=''),
                ),
                migrations.AddField(
                    model_name='alertnotification',
                    name='notification_type',
                    field=models.CharField(default='', max_length=200),
                ),
                migrations.AddField(
                    model_name='alertnotification',
                    name='recipients',
                    field=models.TextField(default=''),
                ),
                migrations.AddField(
                    model_name='alertnotification',
                    name='status',
                    field=models.CharField(choices=[('pending', 'Pending'), ('sent', 'Sent'), ('failed', 'Failed')], default='pending', max_length=20),
                ),
                migrations.AddField(
                    model_name='alertnotification',
                    name='subject',
                    field=models.CharField(blank=True, default='', max_length=500, null=True),
                ),
                migrations.AlterField(
                    model_name='alertnotification',
                    name='alert',
                    field=models.ForeignKey(on_delete=models.CASCADE, related_name='notifications', to='boreas_mediacion.alert'),
                ),
                migrations.AlterField(
                    model_name='alertnotification',
                    name='sent_at',
                    field=models.DateTimeField(blank=True, null=True),
                ),
                migrations.RemoveField(
                    model_name='alertnotification',
                    name='recipient_email',
                ),
                migrations.AlterModelOptions(
                    name='alertnotification',
                    options={'ordering': ['-created_at'], 'verbose_name': 'Alert Notification', 'verbose_name_plural': 'Alert Notifications'},
                ),
            ],
        ),
    ]
