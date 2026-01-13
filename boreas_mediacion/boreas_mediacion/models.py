from django.db import models
# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from . import mqtt


class MQTT_device_family(models.Model):
    name=models.CharField(max_length=100, default='unknown')
    def __str__(self):
        return self.name


class mqtt_msg(models.Model):
    report_time=models.DateTimeField(auto_now=True)
    device=models.JSONField(unique=True, default=dict)
    device_id=models.CharField(max_length=100, default='unknown')
    measures=models.JSONField(default=dict)
    feed=models.CharField(max_length=100, default='unknown')
    device_family=models.ForeignKey(MQTT_device_family, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['device_id']
    def __str__(self):
        return self.device_id

class reported_measure(models.Model):
    report_time=models.DateTimeField(auto_now=True)
    device=models.JSONField(default=dict)
    device_id=models.CharField(max_length=100, default='unknown')
    measures=models.JSONField(default=dict)
    feed=models.CharField(max_length=100, default='unknown')
    
    class Meta:
        unique_together = ['feed', 'device_id']  # Only one record per feed+device_id combination
    
    def __str__(self):
        return f"{self.feed}:{self.device_id}"

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
    device_id=models.ForeignKey(mqtt_msg,on_delete=models.CASCADE,limit_choices_to={'feed__iexact':'shellies','device_id__icontains':'-'})
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
    device_id=models.ForeignKey(mqtt_msg,on_delete=models.CASCADE,limit_choices_to={'feed__iexact':'router'})
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


class DatadisConsumption(models.Model):
    """Datos de consumo eléctrico"""
    supply = models.ForeignKey(DatadisSupply, on_delete=models.CASCADE, related_name='consumption_records')
    
    # Período
    date = models.DateField(db_index=True)
    time = models.CharField(max_length=10, blank=True, null=True, help_text="Hora en formato HH:MM", default='')
    
    # Datos de consumo
    consumption_kwh = models.DecimalField(max_digits=12, decimal_places=3, blank=True, null=True, help_text="Consumo en kWh")
    obtained_method = models.CharField(max_length=50, blank=True, null=True, help_text="Método de obtención")
    
    # Tipo de medida
    measurement_type = models.CharField(max_length=10, default='0', help_text="0: horario, 1: cuartohorario")
    
    # Datos completos
    raw_data = models.JSONField(default=dict, help_text="Datos completos del registro")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date', '-time']
        verbose_name = "DATADIS Consumption"
        verbose_name_plural = "DATADIS Consumptions"
        unique_together = [['supply', 'date', 'time']]
    
    def __str__(self):
        return f"{self.supply.cups} - {self.date} {self.time or ''}: {self.consumption_kwh} kWh"


class DatadisMaxPower(models.Model):
    """Datos de potencia máxima demandada"""
    supply = models.ForeignKey(DatadisSupply, on_delete=models.CASCADE, related_name='max_power_records')
    
    # Período
    date = models.DateField(db_index=True)
    time = models.CharField(max_length=10, blank=True, null=True, default='')
    
    # Datos de potencia
    max_power_kw = models.DecimalField(max_digits=12, decimal_places=3, blank=True, null=True, help_text="Potencia máxima en kW")
    
    # Datos completos
    raw_data = models.JSONField(default=dict)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date', '-time']
        verbose_name = "DATADIS Max Power"
        verbose_name_plural = "DATADIS Max Powers"
        unique_together = [['supply', 'date', 'time']]
    
    def __str__(self):
        return f"{self.supply.cups} - {self.date}: {self.max_power_kw} kW"


# Alert and Monitoring System Models
class AlertRule(models.Model):
    """Regla de alerta para monitorización automática"""
    
    RULE_TYPES = [
        ('disk_space', 'Disk Space'),
        ('device_connection', 'Device Connection'),
        ('aemet_data', 'AEMET Weather Data'),
        ('custom', 'Custom Check'),
    ]
    
    NOTIFICATION_TYPES = [
        ('email', 'Email'),
        ('mqtt', 'MQTT'),
    ]
    
    name = models.CharField(max_length=200, help_text="Nombre de la regla de alerta", default='')
    rule_type = models.CharField(max_length=50, choices=RULE_TYPES, db_index=True, default='custom')
    description = models.TextField(blank=True, null=True, default='')
    
    # Configuración de la regla
    threshold = models.IntegerField(blank=True, null=True, help_text="Umbral para activar alerta (ej: 89 para 89% disco)")
    check_interval_minutes = models.IntegerField(default=60, help_text="Intervalo de verificación en minutos")
    
    # Configuración específica (JSON flexible para diferentes tipos de reglas)
    config = models.JSONField(default=dict, help_text="Configuración específica de la regla")
    
    # Notificaciones
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='email')
    notification_recipients = models.TextField(help_text="Destinatarios separados por comas", default='')
    notification_subject = models.CharField(max_length=500, blank=True, null=True, default='')
    
    # Estado
    active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_check = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = "Alert Rule"
        verbose_name_plural = "Alert Rules"
    
    def __str__(self):
        return f"{self.name} ({self.get_rule_type_display()})"


class Alert(models.Model):
    """Instancia de alerta generada cuando se dispara una regla"""
    
    SEVERITY_LEVELS = [
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('acknowledged', 'Acknowledged'),
        ('resolved', 'Resolved'),
    ]
    
    rule = models.ForeignKey(AlertRule, on_delete=models.CASCADE, related_name='alerts', blank=True, null=True)
    
    # Detalles de la alerta
    alert_type = models.CharField(max_length=50, db_index=True, default='general', blank=True)
    severity = models.CharField(max_length=20, choices=SEVERITY_LEVELS, default='warning')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', db_index=True)
    
    # Mensaje y detalles
    message = models.TextField(default='')
    details = models.JSONField(default=dict, help_text="Detalles adicionales de la alerta")
    
    # Timestamps
    triggered_at = models.DateTimeField(auto_now_add=True, db_index=True)
    acknowledged_at = models.DateTimeField(blank=True, null=True)
    resolved_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-triggered_at']
        verbose_name = "Alert"
        verbose_name_plural = "Alerts"
    
    def __str__(self):
        return f"[{self.severity.upper()}] {self.alert_type} - {self.triggered_at.strftime('%Y-%m-%d %H:%M')}"


class AlertNotification(models.Model):
    """Registro de notificaciones enviadas para alertas"""
    
    NOTIFICATION_STATUS = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    ]
    
    alert = models.ForeignKey(Alert, on_delete=models.CASCADE, related_name='notifications')
    
    # Detalles de la notificación
    notification_type = models.CharField(max_length=200, default='')
    recipients = models.TextField(default='')
    subject = models.CharField(max_length=500, blank=True, null=True, default='')
    message = models.TextField(default='')
    
    # Estado
    status = models.CharField(max_length=20, choices=NOTIFICATION_STATUS, default='pending')
    error_message = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Alert Notification"
        verbose_name_plural = "Alert Notifications"
    
    def __str__(self):
        return f"{self.notification_type} to {self.recipients[:50]} - {self.status}"
