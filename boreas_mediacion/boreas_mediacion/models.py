from django.db import models
from django.utils import timezone
# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from . import mqtt


class MQTT_device_family(models.Model):
    name=models.CharField(max_length=100, default='unknown')
    def __str__(self):
        return self.name



class reported_measure(models.Model):
    report_time = models.DateTimeField(auto_now=True)
    device = models.JSONField(default=dict)
    device_id = models.CharField(max_length=100, default='unknown')
    measures = models.JSONField(default=dict)
    feed = models.CharField(max_length=100, default='unknown')
    device_family_id = models.ForeignKey('MQTT_device_family', null=True, blank=True, on_delete=models.SET_NULL)
    # Link to external DevicesNANOENVI table
    nanoenvi_uuid = models.CharField(max_length=255, null=True, blank=True, help_text='UUID from devicesNANOENVI table')
    nanoenvi_name = models.CharField(max_length=255, null=True, blank=True, help_text='Device name from devicesNANOENVI')
    nanoenvi_client = models.CharField(max_length=255, null=True, blank=True, help_text='Client from devicesNANOENVI')
    
    class Meta:
        unique_together = ['feed', 'device_id']  # Only one record per feed+device_id combination

# --- External Device Monitoring ---
class DeviceMonitoring(models.Model):
    DEVICE_SOURCE_CHOICES = [
        ('nanoenvi', 'NanoENVI'),
        ('co2', 'CO2'),
        ('routers', 'Routers'),
        ('shellies', 'Shellies'),
    ]
    
    uuid = models.CharField(max_length=255)
    source = models.CharField(max_length=50, choices=DEVICE_SOURCE_CHOICES)
    monitored = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['uuid', 'source']
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.source}:{self.uuid} - {'Monitored' if self.monitored else 'Ignored'}"

# --- AEMET API Integration ---
class AemetStation(models.Model):
    station_id = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    province = models.CharField(max_length=100, blank=True, null=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.station_id} - {self.name or ''}"

class AemetData(models.Model):
    station = models.ForeignKey(AemetStation, on_delete=models.CASCADE, related_name='data')
    timestamp = models.DateTimeField()
    data = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['station', 'timestamp']
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.station.station_id} @ {self.timestamp}"

class MQTT_broker(models.Model):
    name=models.CharField(max_length=100, default='unknown')
    server=models.CharField(max_length=100, default='localhost')
    port=models.IntegerField(default=1883)
    keepalive=models.IntegerField(default=60)
    description=models.CharField(max_length=100, default='', blank=True, null=True)
    active=models.BooleanField(default=True)
    user = models.CharField(max_length=100, default='', blank=True, null=True)
    password = models.CharField(max_length=100, default='', blank=True, null=True)
    def __str__(self):
        return self.name

class MQTT_topic(models.Model):
    broker=models.ForeignKey(MQTT_broker,on_delete=models.CASCADE)
    family=models.ForeignKey(MQTT_device_family,on_delete=models.CASCADE)
    topic=models.CharField(max_length=100, default='unknown')
    qos=models.IntegerField(default=0)
    description=models.CharField(max_length=100, default='', blank=True, null=True)
    active=models.BooleanField(default=False)
    ro_rw=models.CharField(max_length=2,default='ro')
    def __str__(self):
        return self.topic

class MQTT_tx(models.Model):
    topic=models.CharField(max_length=100, default='unknown')
    payload=models.CharField(max_length=1000, default='', blank=True, null=True)

    def __str__(self):
        return self.topic.topic
class MQTT_feed(models.Model):
    name=models.CharField(max_length=100, default='unknown')
    description=models.CharField(max_length=100, default='', blank=True, null=True)
    topic=models.ForeignKey(MQTT_topic,on_delete=models.CASCADE)
    def __str__(self):
        return self.name

class sensor_actuacion(models.Model):
    tipo=models.CharField(max_length=100, default='unknown')
    command=models.CharField(max_length=100, default='', blank=True, null=True)
    parameter=models.CharField(max_length=100, default='', blank=True, null=True)
    description=models.CharField(max_length=100, default='', blank=True, null=True)
    def __str__(self):
        return self.tipo
class sensor_command(models.Model):
    actuacion=models.ForeignKey(sensor_actuacion,on_delete=models.CASCADE)
    # device_id=models.ForeignKey(mqtt_msg,on_delete=models.CASCADE,limit_choices_to={'feed__iexact':'shellies','device_id__icontains':'-'})
    device_id=models.CharField(max_length=100, default='unknown')
    circuit=models.IntegerField(default=0)

    def __str__(self):
        return self.actuacion.description

class router_parameter(models.Model):
    parameter=models.CharField(max_length=100, default='unknown')
    description=models.CharField(max_length=100, default='', blank=True, null=True)
    def __str__(self):
        return self.parameter
class router_get(models.Model):
    parameter=models.ForeignKey(router_parameter,on_delete=models.CASCADE)
    # device_id=models.ForeignKey(mqtt_msg,on_delete=models.CASCADE,limit_choices_to={'feed__iexact':'router'})
    # If needed, add a new field for router device_id
    def __str__(self):
        return self.parameter.parameter+'_'+self.device_id.device_id


# WirelessLogic SIMPro API Models
class WirelessLogic_SIM(models.Model):
    """Modelo para almacenar información de tarjetas SIM de WirelessLogic"""
    # Identificadores principales
    iccid = models.CharField(max_length=20, unique=True, db_index=True, help_text="Integrated Circuit Card Identifier", default='')
    msisdn = models.CharField(max_length=20, blank=True, null=True, help_text="Mobile Station International Subscriber Directory Number", default='')
    imsi = models.CharField(max_length=20, blank=True, null=True, help_text="International Mobile Subscriber Identity", default='')
    
    # Información de estado
    status = models.CharField(max_length=50, blank=True, null=True, help_text="Estado actual de la SIM", default='')
    activation_date = models.DateTimeField(blank=True, null=True, help_text="Fecha de activación")
    
    # Información de tarifa y cuenta
    tariff_name = models.CharField(max_length=200, blank=True, null=True, default='')
    account_name = models.CharField(max_length=200, blank=True, null=True, default='')
    
    # Información de red
    network = models.CharField(max_length=100, blank=True, null=True, default='')
    roaming_network = models.CharField(max_length=100, blank=True, null=True, default='')
    
    # Datos completos en JSON (para campos adicionales)
    raw_data = models.JSONField(default=dict, help_text="Datos completos de la API")
    
    # Metadatos
    last_sync = models.DateTimeField(auto_now=True, help_text="Última sincronización con la API")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-last_sync']
        verbose_name = "WirelessLogic SIM"
        verbose_name_plural = "WirelessLogic SIMs"
    
    def __str__(self):
        return f"{self.iccid} ({self.msisdn or 'Sin MSISDN'})"


class WirelessLogic_Usage(models.Model):
    """Modelo para almacenar datos de uso de SIMs"""
    sim = models.ForeignKey(WirelessLogic_SIM, on_delete=models.CASCADE, related_name='usage_records')
    
    # Período de uso
    period_start = models.DateTimeField(help_text="Inicio del período")
    period_end = models.DateTimeField(help_text="Fin del período")
    
    # Datos de uso
    data_used_mb = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Datos usados en MB")
    sms_sent = models.IntegerField(default=0)
    sms_received = models.IntegerField(default=0)
    voice_minutes = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Costos
    total_cost = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)
    currency = models.CharField(max_length=3, default='EUR')
    
    # Datos completos en JSON
    raw_data = models.JSONField(default=dict, help_text="Datos completos de uso")
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-period_end']
        verbose_name = "WirelessLogic Usage"
        verbose_name_plural = "WirelessLogic Usages"
        unique_together = [['sim', 'period_start', 'period_end']]
    
    def __str__(self):
        return f"{self.sim.iccid} - {self.period_start.date()} to {self.period_end.date()}"


# Sigfox sensor models
class SigfoxDevice(models.Model):
    """Dispositivo Sigfox (sensor)"""
    device_id = models.CharField(max_length=50, unique=True, db_index=True, default='')
    firmware = models.CharField(max_length=10, blank=True, null=True, default='')
    last_seen = models.DateTimeField(blank=True, null=True)
    last_payload = models.JSONField(default=dict, blank=True)

    # Últimas mediciones básicas
    last_co2 = models.IntegerField(blank=True, null=True)
    last_temp = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    last_hum = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    last_base = models.IntegerField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = "Sigfox Device"
        verbose_name_plural = "Sigfox Devices"

    def __str__(self):
        return self.device_id


class SigfoxReading(models.Model):
    """Lecturas individuales de sensores Sigfox"""
    device = models.ForeignKey(SigfoxDevice, on_delete=models.CASCADE, related_name='readings')
    timestamp = models.DateTimeField()
    firmware = models.CharField(max_length=10, blank=True, null=True, default='')

    co2 = models.IntegerField(blank=True, null=True)
    temp = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    hum = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    base = models.IntegerField(blank=True, null=True)

    raw_data = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Sigfox Reading"
        verbose_name_plural = "Sigfox Readings"

    def __str__(self):
        return f"{self.device.device_id} @ {self.timestamp}"


# DATADIS models for Spanish electricity consumption data
class DatadisCredentials(models.Model):
    """Credenciales para acceso a la API de DATADIS"""
    username = models.CharField(max_length=100, unique=True, help_text="NIF/CIF del usuario", default='')
    password = models.CharField(max_length=200, help_text="Contraseña de acceso", default='')
    
    # Token de autenticación
    auth_token = models.TextField(blank=True, null=True, help_text="Token Bearer de autenticación", default='')
    token_expires_at = models.DateTimeField(blank=True, null=True)
    
    # Estado
    active = models.BooleanField(default=True)
    last_auth = models.DateTimeField(blank=True, null=True, help_text="Última autenticación exitosa")
    last_sync = models.DateTimeField(blank=True, null=True, help_text="Última sincronización de datos")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "DATADIS Credentials"
        verbose_name_plural = "DATADIS Credentials"
    
    def __str__(self):
        return f"{self.username}"


class DatadisSupply(models.Model):
    """Punto de suministro (CUPS) de electricidad"""
    credentials = models.ForeignKey(DatadisCredentials, on_delete=models.CASCADE, related_name='supplies')
    
    # Identificadores
    cups = models.CharField(max_length=22, unique=True, db_index=True, help_text="Código Universal de Punto de Suministro", default='')
    
    # Ubicación
    address = models.CharField(max_length=500, blank=True, null=True, default='')
    postal_code = models.CharField(max_length=10, blank=True, null=True, default='')
    province = models.CharField(max_length=100, blank=True, null=True, default='')
    municipality = models.CharField(max_length=200, blank=True, null=True, default='')
    
    # Detalles técnicos
    distributor = models.CharField(max_length=100, blank=True, null=True, default='')
    distributor_code = models.CharField(max_length=10, blank=True, null=True, default='')
    point_type = models.IntegerField(blank=True, null=True, help_text="Tipo de punto: 1-5")
    
    # Fechas de validez
    valid_date_from = models.DateField(blank=True, null=True)
    valid_date_to = models.DateField(blank=True, null=True)
    
    # Estado
    active = models.BooleanField(default=True)
    
    # Datos completos
    raw_data = models.JSONField(default=dict, help_text="Datos completos de la API")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['cups']
        verbose_name = "DATADIS Supply Point"
        verbose_name_plural = "DATADIS Supply Points"
    
    def __str__(self):
        return f"{self.cups} ({self.address or 'Sin dirección'})"








class TopicMessageTimeout(models.Model):
    """Configuración de alertas por timeout de mensajes en tópicos"""
    
    topic = models.CharField(max_length=255, unique=True, db_index=True, help_text="Tópico MQTT a monitorear")
    timeout_minutes = models.IntegerField(default=60, help_text="Minutos sin mensajes antes de alerta")
    active = models.BooleanField(default=True)
    
    # Último mensaje recibido
    last_message_time = models.DateTimeField(blank=True, null=True, help_text="Hora del último mensaje recibido")
    alert_sent = models.BooleanField(default=False, help_text="Si ya se envió alerta por timeout")
    alert_sent_at = models.DateTimeField(blank=True, null=True, help_text="Cuándo se envió la última alerta")
    
    # Notificación
    notification_recipients = models.TextField(help_text="Destinatarios separados por comas", default='')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['topic']
        verbose_name = "Topic Message Timeout"
        verbose_name_plural = "Topic Message Timeouts"
    
    def __str__(self):
        return f"{self.topic} (timeout: {self.timeout_minutes}min)"
    
    def is_timed_out(self):
        """Verificar si el tópico está en timeout"""
        if not self.last_message_time:
            return True
        from datetime import timedelta
        timeout_threshold = timezone.now() - timedelta(minutes=self.timeout_minutes)
        return self.last_message_time < timeout_threshold


class SystemConfiguration(models.Model):
    """Configuración general del sistema"""
    
    CONFIG_TYPES = [
        ('email', 'Email Configuration'),
        ('alert', 'Alert Configuration'),
        ('airflow', 'Airflow Configuration'),
        ('general', 'General Configuration'),
    ]
    
    config_type = models.CharField(max_length=50, choices=CONFIG_TYPES, default='general')
    key = models.CharField(max_length=100, unique=True, db_index=True, help_text="Clave de configuración (ej: airflow_alert_email)", default='')
    value = models.TextField(help_text="Valor de la configuración", default='')
    description = models.TextField(blank=True, null=True, default='', help_text="Descripción de la configuración")
    
    # Metadatos
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['config_type', 'key']
        verbose_name = "System Configuration"
        verbose_name_plural = "System Configurations"
    
    def __str__(self):
        return f"{self.key} = {self.value[:50]}"
    
    @classmethod
    def get_value(cls, key, default=None):
        """Obtener valor de configuración por clave"""
        try:
            config = cls.objects.get(key=key, active=True)
            return config.value
        except cls.DoesNotExist:
            return default
    
    @classmethod
    def set_value(cls, key, value, config_type='general', description=''):
        """Establecer o actualizar valor de configuración"""
        config, created = cls.objects.update_or_create(
            key=key,
            defaults={
                'value': value,
                'config_type': config_type,
                'description': description,
                'active': True
            }
        )
        return config
