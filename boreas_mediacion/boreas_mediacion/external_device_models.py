from django.db import models


class ExternalDevice(models.Model):
    device_id = models.CharField(max_length=255, unique=True, db_index=True, db_column='device_id')
    uuid = models.CharField(max_length=255, db_column='uuid', blank=True, null=True)
    uuid_ip = models.CharField(max_length=255, db_column='uuid_ip', blank=True, null=True)
    name = models.CharField(max_length=255, db_column='name', blank=True, null=True)
    alias = models.CharField(max_length=255, db_column='alias', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'boreas_mediacion_external_devices'
        verbose_name = 'External Device'
        verbose_name_plural = 'External Devices'
        ordering = ['device_id']

    def __str__(self):
        return self.device_id

# ExternalDeviceMapping reference removed
