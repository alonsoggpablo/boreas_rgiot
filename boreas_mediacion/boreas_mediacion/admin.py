from django.contrib import admin, messages
from django.contrib.admin import SimpleListFilter
from .models import MQTT_device_family, MQTT_broker, MQTT_feed, sensor_command, sensor_actuacion, router_get, \
    router_parameter, reported_measure, WirelessLogic_SIM, WirelessLogic_Usage, SigfoxDevice, SigfoxReading, \
    DatadisCredentials, DatadisSupply, SystemConfiguration, DeviceMonitoring, DetectedAnomaly, DeviceTypeMapping, ExternalDeviceMapping

@admin.register(MQTT_device_family)
class MQTTDeviceFamilyAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')

# Custom filters for DeviceMonitoring - uses local ExternalDeviceMapping table
class DeviceNameFilter(SimpleListFilter):
    title = 'Device Name'
    parameter_name = 'device_name'

    def lookups(self, request, model_admin):
        """Get unique device names from ExternalDeviceMapping (external_alias if available)"""
        names = set()
        for alias in ExternalDeviceMapping.objects.filter(external_alias__isnull=False).values_list('external_alias', flat=True):
            if alias:
                names.add(alias)
        return [(name, name) for name in sorted(names)]

    def queryset(self, request, queryset):
        if self.value():
            # Get external_device_ids matching this alias from ExternalDeviceMapping
            uuids = set(ExternalDeviceMapping.objects.filter(external_alias=self.value()).values_list('external_device_id', flat=True))
            return queryset.filter(uuid__in=uuids) if uuids else queryset
        return queryset


class DeviceClientFilter(SimpleListFilter):
    title = 'Device Client'
    parameter_name = 'device_client'

    def lookups(self, request, model_admin):
        """Get unique clients from ExternalDeviceMapping"""
        clients = set(ExternalDeviceMapping.objects.filter(client_name__isnull=False).values_list('client_name', flat=True))
        return [(client, client) for client in sorted(clients) if client]

    def queryset(self, request, queryset):
        if self.value():
            # Get external_device_ids matching this client from ExternalDeviceMapping
            uuids = set(ExternalDeviceMapping.objects.filter(client_name=self.value()).values_list('external_device_id', flat=True))
            return queryset.filter(uuid__in=uuids) if uuids else queryset
        return queryset

# Register reported_measure in admin
@admin.register(reported_measure)
class ReportedMeasureAdmin(admin.ModelAdmin):
    list_display = ('device_id', 'feed', 'measures', 'nanoenvi_name', 'nanoenvi_client', 'family', 'report_time')
    list_filter = ('device_family_id', 'nanoenvi_client', 'report_time')
    search_fields = ('device_id', 'feed', 'measures', 'report_time', 'nanoenvi_uuid', 'nanoenvi_name', 'nanoenvi_client')

    def family(self, obj):
        return obj.device_family_id.name if obj.device_family_id else None
    family.admin_order_field = 'device_family_id'
    family.short_description = 'Family'

# Register DeviceMonitoring in admin
@admin.register(DeviceMonitoring)
class DeviceMonitoringAdmin(admin.ModelAdmin):
    list_display = ('uuid', 'device_type', 'device_name', 'device_client', 'monitored', 'updated_at')
    list_filter = (DeviceClientFilter, DeviceNameFilter, 'monitored', 'updated_at')
    search_fields = ('uuid',)
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'updated_at'
    actions = ['mark_monitored', 'mark_not_monitored']
    # Show client and filter external_device choices by client in creation form
    def get_fields(self, request, obj=None):
        if obj is None:
            return ['external_device', 'monitored']
        return ['uuid', 'external_device', 'monitored', 'created_at', 'updated_at']

    # Use default form, show all external devices

    def device_type(self, obj):
        return obj.device_type or '-'
    device_type.short_description = 'Type'

    def device_name(self, obj):
        """Fetch name from linked ExternalDeviceMapping"""
        if obj.external_device:
            return obj.external_device.external_alias or obj.external_device.external_device_id
        return obj.uuid
    device_name.short_description = 'Name'

    def device_client(self, obj):
        """Fetch client from linked ExternalDeviceMapping"""
        if obj.external_device and obj.external_device.client_name:
            return obj.external_device.client_name
        return '-'
    device_client.short_description = 'Client'

    def mark_monitored(self, request, queryset):
        updated = queryset.update(monitored=True)
        self.message_user(request, f"{updated} device(s) marked as monitored.")
    mark_monitored.short_description = "Mark selected as monitored"

    def mark_not_monitored(self, request, queryset):
        updated = queryset.update(monitored=False)
        self.message_user(request, f"{updated} device(s) marked as not monitored.")
    mark_not_monitored.short_description = "Mark selected as not monitored"


# ====================
#   MQTT READS
# ====================
from django.urls import reverse
from django.utils.html import format_html
from django.http import HttpResponseRedirect
from django.utils import timezone
import logging
from .models import MQTT_topic
admin.site.register(MQTT_topic)
@admin.register(MQTT_broker)
class MQTTBrokerAdmin(admin.ModelAdmin):
    list_display = ('name', 'server', 'port', 'active')
from .models import AemetStation, AemetData
# --- AEMET API Models ---
@admin.register(AemetStation)
class AemetStationAdmin(admin.ModelAdmin):
    list_display = ('station_id', 'name', 'province', 'active', 'created_at', 'updated_at')
    list_filter = ('active', 'province')
    search_fields = ('station_id', 'name', 'province')

    actions = ['activate_stations', 'deactivate_stations']

    def activate_stations(self, request, queryset):
        updated = queryset.update(active=True)
        self.message_user(request, f"{updated} station(s) activated.")
    activate_stations.short_description = "Activate selected stations"

    def deactivate_stations(self, request, queryset):
        updated = queryset.update(active=False)
        self.message_user(request, f"{updated} station(s) deactivated.")
    deactivate_stations.short_description = "Deactivate selected stations"

@admin.register(AemetData)
class AemetDataAdmin(admin.ModelAdmin):
    list_display = ('station', 'timestamp', 'created_at')
    list_filter = ('station',)
    search_fields = ('station__station_id',)
from .wirelesslogic_service import WirelessLogicService
from .datadis_service import DatadisService

from django.urls import reverse
from django.utils.html import format_html

class router_parameter_Admin(admin.ModelAdmin):
    class Meta:
        app_label = 'MQTT READS'
    list_display = ('parameter','description')
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs

    def _parse_payload(self, data_hex):
        # Parses hex payload into metrics; mirrors Sigfox callback logic.
        fw = data_hex[0:1] or None
        temp = hum = co2 = base = None
        try:
            temp = round((int(data_hex[2:6], 16) / 10) - 40, 2)
            hum = int(data_hex[6:8], 16)
            co2 = int(data_hex[8:12], 16)
            base = int(data_hex[12:14], 16)
        except Exception:
            pass
        return fw, temp, hum, co2, base



admin.site.register(router_parameter, router_parameter_Admin)



@admin.register(SigfoxReading)
class SigfoxReadingAdmin(admin.ModelAdmin):
    class Meta:
        app_label = 'API READS'
    list_display = ('device_link', 'timestamp', 'co2', 'temp', 'hum', 'base')
    list_filter = ('timestamp',)
    search_fields = ('device__device_id',)
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'timestamp'

    def device_link(self, obj):
        url = reverse('admin:boreas_mediacion_sigfoxdevice_change', args=[obj.device.id])
        return format_html('<a href="{}">{}</a>', url, obj.device.device_id)
    device_link.short_description = 'Device'
    device_link.admin_order_field = 'device__device_id'


# DATADIS Admin
@admin.register(DatadisCredentials)
class DatadisCredentialsAdmin(admin.ModelAdmin):
    class Meta:
        app_label = 'API READS'
    list_display = ('username', 'active', 'last_auth', 'last_sync', 'token_status')
    list_filter = ('active', 'last_auth')
    search_fields = ('username',)
    readonly_fields = ('auth_token', 'token_expires_at', 'last_auth', 'last_sync', 'created_at', 'updated_at')
    actions = ['authenticate_action', 'sync_supplies_action', 'sync_consumption_action']
    
    fieldsets = (
        ('Credenciales', {
            'fields': ('username', 'password', 'active')
        }),
        ('Token de Autenticación', {
            'fields': ('auth_token', 'token_expires_at', 'last_auth'),
            'classes': ('collapse',)
        }),
        ('Sincronización', {
            'fields': ('last_sync',)
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def token_status(self, obj):
        # Mostrar estado del token
        if not obj.auth_token:
            return format_html('<span style="color: gray;">● Sin token</span>')
        
        if obj.token_expires_at and timezone.now() > obj.token_expires_at:
            return format_html('<span style="color: red;">● Expirado</span>')
        
        return format_html('<span style="color: green;">● Válido</span>')
    token_status.short_description = 'Estado Token'
    
    def authenticate_action(self, request, queryset):
        # Autenticar y obtener token
        for credentials in queryset:
            try:
                service = DatadisService(credentials)
                token = service.authenticate()
                self.message_user(
                    request,
                    f'Autenticación exitosa para {credentials.username}. Token obtenido.',
                    level=messages.SUCCESS
                )
            except Exception as e:
                self.message_user(
                    request,
                    f'Error autenticando {credentials.username}: {str(e)}',
                    level=messages.ERROR
                )
    authenticate_action.short_description = "🔑 Autenticar y obtener token"
    
    def sync_supplies_action(self, request, queryset):
        # Sincronizar puntos de suministro
        for credentials in queryset:
            try:
                service = DatadisService(credentials)
                created, updated = service.sync_supplies()
                self.message_user(
                    request,
                    f'{credentials.username}: {created} CUPS creados, {updated} actualizados',
                    level=messages.SUCCESS
                )
            except Exception as e:
                self.message_user(
                    request,
                    f'Error sincronizando supplies para {credentials.username}: {str(e)}',
                    level=messages.ERROR
                )
    sync_supplies_action.short_description = "⟳ Sincronizar CUPS"
    
    def sync_consumption_action(self, request, queryset):
        # Sincronizar consumo del mes actual
        for credentials in queryset:
            try:
                service = DatadisService(credentials)
                results = service.sync_all_supplies_consumption()
                self.message_user(
                    request,
                    f'{credentials.username}: {results["consumption_records"]} registros de consumo, '
                    f'{results["max_power_records"]} registros de potencia',
                    level=messages.SUCCESS
                )
            except Exception as e:
                self.message_user(
                    request,
                    f'Error sincronizando consumo para {credentials.username}: {str(e)}',
                    level=messages.ERROR
                )
    sync_consumption_action.short_description = "📊 Sincronizar consumo (mes actual)"


@admin.register(DatadisSupply)
class DatadisSupplyAdmin(admin.ModelAdmin):
    class Meta:
        app_label = 'API READS'
    list_display = ('cups', 'address_short', 'province', 'distributor', 'point_type', 'active', 'last_read_time')

    def last_read_time(self, obj):
        # Use updated_at as the last read time since consumption records are deleted
        return obj.updated_at
    last_read_time.short_description = 'Last Read Time'
    list_filter = ('active', 'province', 'distributor', 'point_type')
    search_fields = ('cups', 'address', 'postal_code', 'municipality')
    readonly_fields = ('created_at', 'updated_at', 'raw_data')
    actions = ['sync_consumption_action', 'sync_max_power_action', 'activate_supplies', 'deactivate_supplies']
    
    fieldsets = (
        ('Identificación', {
            'fields': ('cups', 'credentials', 'active')
        }),
        ('Ubicación', {
            'fields': ('address', 'postal_code', 'province', 'municipality')
        }),
        ('Detalles Técnicos', {
            'fields': ('distributor', 'distributor_code', 'point_type')
        }),
        ('Validez', {
            'fields': ('valid_date_from', 'valid_date_to')
        }),
        ('Datos Raw', {
            'fields': ('raw_data',),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def address_short(self, obj):
        # Dirección abreviada
        if obj.address and len(obj.address) > 50:
            return obj.address[:47] + '...'
        return obj.address or '-'
    address_short.short_description = 'Dirección'
    
    
    def sync_consumption_action(self, request, queryset):
        # Sincronizar consumo del mes actual
        for supply in queryset:
            try:
                service = DatadisService(supply.credentials)
                count = service.sync_consumption_data(supply)
                self.message_user(
                    request,
                    f'{supply.cups}: {count} registros de consumo sincronizados',
                    level=messages.SUCCESS
                )
            except Exception as e:
                self.message_user(
                    request,
                    f'Error sincronizando {supply.cups}: {str(e)}',
                    level=messages.ERROR
                )
    sync_consumption_action.short_description = "📊 Sincronizar consumo"
    
    def sync_max_power_action(self, request, queryset):
        # Sincronizar potencia máxima
        for supply in queryset:
            try:
                service = DatadisService(supply.credentials)
                count = service.sync_max_power(supply)
                self.message_user(
                    request,
                    f'{supply.cups}: {count} registros de potencia sincronizados',
                    level=messages.SUCCESS
                )
            except Exception as e:
                self.message_user(
                    request,
                    f'Error sincronizando potencia para {supply.cups}: {str(e)}',
                    level=messages.ERROR
                )
    sync_max_power_action.short_description = "⚡ Sincronizar potencia máxima"
    
    def activate_supplies(self, request, queryset):
        # Activar supplies seleccionados
        updated = queryset.update(active=True)
        self.message_user(request, f'{updated} CUPS activados')
    activate_supplies.short_description = "✓ Activar CUPS"
    
    def deactivate_supplies(self, request, queryset):
        # Desactivar supplies seleccionados
        updated = queryset.update(active=False)
        self.message_user(request, f'{updated} CUPS desactivados')
    deactivate_supplies.short_description = "✗ Desactivar CUPS"


@admin.register(SigfoxDevice)
class SigfoxDeviceAdmin(admin.ModelAdmin):
    class Meta:
        app_label = 'API READS'
    list_display = ('device_id', 'firmware', 'last_seen', 'last_co2', 'last_temp', 'last_hum', 'last_read_time')
    search_fields = ('device_id',)
    readonly_fields = ('created_at', 'updated_at')
    actions = ['create_test_reading', 'show_recent_readings']

    def last_read_time(self, obj):
        latest = obj.readings.order_by('-timestamp').first()
        return latest.timestamp if latest else None
    last_read_time.short_description = 'Last Read Time'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs

    def _parse_payload(self, data_hex):
        fw = data_hex[0:1] or None
        temp = hum = co2 = base = None
        try:
            temp = round((int(data_hex[2:6], 16) / 10) - 40, 2)
            hum = int(data_hex[6:8], 16)
            co2 = int(data_hex[8:12], 16)
            base = int(data_hex[12:14], 16)
        except Exception:
            pass
        return fw, temp, hum, co2, base

    def create_test_reading(self, request, queryset):
        sample_hex = '102d0501f40f'
        created = 0
        now = timezone.now()
        for device in queryset:
            fw, temp, hum, co2, base = self._parse_payload(sample_hex)
            payload = {'device': device.device_id, 'data': sample_hex, 'timestamp': int(now.timestamp())}
            SigfoxReading.objects.create(
                device=device,
                timestamp=now,
                firmware=fw,
                co2=co2,
                temp=temp,
                hum=hum,
                base=base,
                raw_data=payload
            )
            device.firmware = fw or device.firmware
            device.last_seen = now
            device.last_payload = payload
            device.last_co2 = co2
            device.last_temp = temp
            device.last_hum = hum
            device.last_base = base
            device.save(update_fields=['firmware', 'last_seen', 'last_payload', 'last_co2', 'last_temp', 'last_hum', 'last_base', 'updated_at'])
            created += 1
        self.message_user(request, f'Lecturas de prueba creadas para {created} dispositivo(s)', level=messages.SUCCESS)
    create_test_reading.short_description = "⚙️ Crear lectura de prueba"

    def show_recent_readings(self, request, queryset):
        summaries = []
        for device in queryset:
            latest = device.readings.order_by('-timestamp').first()
            if latest:
                summaries.append(f"{device.device_id}: CO2={latest.co2}, temp={latest.temp}, hum={latest.hum} @ {latest.timestamp:%Y-%m-%d %H:%M}")
            else:
                summaries.append(f"{device.device_id}: sin lecturas")
        msg = '; '.join(summaries[:10])
        self.message_user(request, msg, level=messages.INFO)
    show_recent_readings.short_description = "👀 Ver últimas lecturas"

class MQTTTopicAdmin(admin.ModelAdmin):
    list_display = ('topic', 'broker', 'family', 'qos', 'active', 'ro_rw', 'description')
    list_filter = ('broker', 'family', 'active', 'ro_rw', 'qos')
    search_fields = ('topic', 'description')

    actions = ['activate_topics', 'deactivate_topics']

    def activate_topics(self, request, queryset):
        updated = queryset.update(active=True)
        self.message_user(request, f"{updated} topic(s) activated.")
    activate_topics.short_description = "Activate selected topics"

    def deactivate_topics(self, request, queryset):
        updated = queryset.update(active=False)
        self.message_user(request, f"{updated} topic(s) deactivated.")
    deactivate_topics.short_description = "Deactivate selected topics"

admin.site.unregister(MQTT_topic)
admin.site.register(MQTT_topic, MQTTTopicAdmin)

@admin.register(WirelessLogic_SIM)
class WirelessLogicSIMAdmin(admin.ModelAdmin):
    list_display = ('iccid', 'msisdn', 'imsi', 'status', 'activation_date', 'tariff_name', 'account_name', 'network', 'last_sync', 'created_at', 'updated_at')
    search_fields = ('iccid', 'msisdn', 'imsi', 'account_name')
    list_filter = ('status', 'network', 'tariff_name', 'activation_date')
    readonly_fields = ('created_at', 'updated_at', 'last_sync')

@admin.register(WirelessLogic_Usage)
class WirelessLogicUsageAdmin(admin.ModelAdmin):
    list_display = ('sim', 'period_start', 'period_end', 'data_used_mb', 'sms_sent', 'sms_received', 'voice_minutes', 'total_cost', 'currency', 'created_at', 'updated_at')
    search_fields = ('sim__iccid', 'sim__msisdn')
    list_filter = ('period_start', 'period_end', 'currency', 'sim__status')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(DetectedAnomaly)
class DetectedAnomalyAdmin(admin.ModelAdmin):
    list_display = ('detected_at', 'device_name', 'device_id', 'client', 'metric_name', 'metric_value', 'anomaly_type', 'severity', 'baseline_mean')
    list_filter = ('anomaly_type', 'client', 'detected_at', 'metric_name')
    search_fields = ('device_name', 'device_id', 'client', 'metric_name')
    readonly_fields = ('detected_at', 'created_at', 'details')
    date_hierarchy = 'detected_at'
    ordering = ('-detected_at',)
    
    fieldsets = (
        ('Device Information', {
            'fields': ('device_name', 'device_id', 'client')
        }),
        ('Metric Details', {
            'fields': ('metric_name', 'metric_value', 'anomaly_type', 'severity')
        }),
        ('Baseline Statistics', {
            'fields': ('baseline_mean', 'baseline_std')
        }),
        ('Detection Metadata', {
            'fields': ('detected_at', 'created_at', 'details'),
            'classes': ('collapse',)
        }),
    )


# --- External Device Integration Admin ---

@admin.register(DeviceTypeMapping)
class DeviceTypeMappingAdmin(admin.ModelAdmin):
    list_display = ('external_device_type_name', 'get_mqtt_family', 'created_at')
    list_filter = ('created_at', 'mqtt_device_family')
    search_fields = ('external_device_type_name',)
    raw_id_fields = ('mqtt_device_family',)
    readonly_fields = ('created_at',)
    fieldsets = (
        ('Device Type Information', {
            'fields': ('external_device_type_name', 'mqtt_device_family')
        }),
        ('Audit Information', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    def get_mqtt_family(self, obj):
        return obj.mqtt_device_family.name if obj.mqtt_device_family else "—"
    get_mqtt_family.short_description = 'MQTT Family'


class DeviceTypeFilter(SimpleListFilter):
    title = 'Device Type'
    parameter_name = 'device_type'

    def lookups(self, request, model_admin):
        # Get unique device types from metadata
        device_types = set()
        for record in ExternalDeviceMapping.objects.all():
            device_type = record.metadata.get('device_type')
            if device_type:
                device_types.add(device_type)
        return [(dt, dt) for dt in sorted(device_types)]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(metadata__device_type=self.value())
        return queryset


@admin.register(ExternalDeviceMapping)
class ExternalDeviceMappingAdmin(admin.ModelAdmin):
    list_display = (
        'external_device_id',
        'external_alias',
        'client_name',
        'group_name',
        'device_type_display',
        'status',
        'is_active',
        'updated_at'
    )
    list_filter = (
        'status',
        DeviceTypeFilter,
        'is_active',
        'client_name',
        'group_name',
        'created_at',
        'updated_at'
    )
    search_fields = ('external_device_id', 'external_alias', 'client_name', 'location_name', 'group_name')
    readonly_fields = ('created_at', 'updated_at', 'metadata_display', 'device_type_display', 'group_name_display', 'crawl_date_display')
    date_hierarchy = 'updated_at'
    
    fieldsets = (
        ('Device Identification', {
            'fields': ('external_device_id', 'external_alias', 'internal_device_uuid')
        }),
        ('Organization & Location', {
            'fields': ('client_name', 'location_name', 'group_name')
        }),
        ('Device Status', {
            'fields': ('status', 'is_active'),
            'description': 'Current status and activity state of the device'
        }),
        ('Device Lifecycle', {
            'fields': ('purchase_date', 'sale_date'),
            'description': 'Purchase and disposal dates'
        }),
        ('Device Metadata', {
            'fields': ('device_type_display', 'group_name_display', 'crawl_date_display', 'metadata'),
            'classes': ('wide',)
        }),
        ('Audit Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def device_type_display(self, obj):
        return obj.device_type or "—"
    device_type_display.short_description = 'Device Type (from metadata)'

    def group_name_display(self, obj):
        return obj.metadata.get('group_name', '—')
    group_name_display.short_description = 'Group Name (from metadata)'

    def crawl_date_display(self, obj):
        return obj.crawl_date if obj.crawl_date else "—"
    crawl_date_display.short_description = 'Crawl Date (from metadata)'

    def metadata_display(self, obj):
        import json
        return f'<pre style="background: #f5f5f5; padding: 10px; border-radius: 4px; overflow-x: auto;">{json.dumps(obj.metadata, indent=2, ensure_ascii=False)}</pre>'
    metadata_display.short_description = 'Metadata (JSON)'
    metadata_display.allow_tags = True

    actions = ['activate_devices', 'deactivate_devices', 'bulk_assign_group']

    def activate_devices(self, request, queryset):
        """Bulk activate selected devices"""
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            f'✓ {updated} device(s) activated',
            messages.SUCCESS
        )
    activate_devices.short_description = "✓ Activate selected devices"

    def deactivate_devices(self, request, queryset):
        """Bulk deactivate selected devices"""
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            f'⛔ {updated} device(s) deactivated',
            messages.WARNING
        )
    deactivate_devices.short_description = "⛔ Deactivate selected devices"

    def bulk_assign_group(self, request, queryset):
        """Placeholder for bulk group assignment"""
        self.message_user(
            request,
            'Bulk group assignment feature coming soon',
            messages.INFO
        )
    bulk_assign_group.short_description = "📁 Assign group to selected devices"

