# ====================
#   MQTT READS
# ====================
from django.contrib import admin, messages
from django.urls import reverse
from django.utils.html import format_html
from django.http import HttpResponseRedirect
from django.utils import timezone
import logging
from .models import mqtt_msg, MQTT_device_family, MQTT_broker, MQTT_feed, sensor_command, sensor_actuacion, router_get, \
    router_parameter, reported_measure, WirelessLogic_SIM, WirelessLogic_Usage, SigfoxDevice, SigfoxReading, \
    DatadisCredentials, DatadisSupply, SystemConfiguration
from .models import MQTT_topic
admin.site.register(MQTT_topic)
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
from . import mqtt as mqtt_module
from .wirelesslogic_service import WirelessLogicService
from .datadis_service import DatadisService

from django.urls import reverse
from django.utils.html import format_html

class MQTT_MSG_Admin(admin.ModelAdmin):
    class Meta:
        app_label = 'MQTT READS'
    list_display = ('device_id','device','measures','feed','device_family','report_time')
    list_filter = ('feed','report_time','device_id','device_family')
    search_fields = ('device_id','device','measures','report_time')

admin.site.register(mqtt_msg, MQTT_MSG_Admin)
#register router_parameter
class router_parameter_Admin(admin.ModelAdmin):
    class Meta:
        app_label = 'MQTT READS'
    list_display = ('parameter','description')
    list_filter = ('parameter','description')
    search_fields = ('parameter','description')
admin.site.register(router_parameter,router_parameter_Admin)

#register reported_measure
class reported_measure_Admin(admin.ModelAdmin):
    class Meta:
        app_label = 'MQTT READS'
    list_display = ('feed','device_id','measures','report_time')
    list_filter = ('feed','report_time','device_id')
    search_fields = ('device_id','measures','report_time')
admin.site.register(reported_measure,reported_measure_Admin)

# ====================
#   API READS
# ====================


# WirelessLogic Admin
@admin.register(WirelessLogic_SIM)
class WirelessLogic_SIM_Admin(admin.ModelAdmin):
    class Meta:
        app_label = 'API READS'
    list_display = ('iccid', 'msisdn', 'status', 'tariff_name', 'network', 'activation_date', 'updated_at')
    list_filter = ('status', 'network', 'tariff_name', 'activation_date')
    search_fields = ('iccid', 'msisdn', 'imsi', 'account_name')
    readonly_fields = ('created_at', 'updated_at')
    actions = ['sync_selected_sims', 'sync_all_sims_action']
    
    fieldsets = (
        ('Información Principal', {
            'fields': ('iccid', 'msisdn', 'imsi', 'status')
        }),
        ('Detalles de Red', {
            'fields': ('network', 'roaming_network', 'tariff_name', 'account_name')
        }),
        ('Fechas', {
            'fields': ('activation_date', 'created_at', 'updated_at')
        }),
        ('Datos Raw', {
            'fields': ('raw_data',),
            'classes': ('collapse',)
        }),
    )
    
    def sync_selected_sims(self, request, queryset):
        # Sincronizar SIMs seleccionadas desde la API
        try:
            service = WirelessLogicService()
            iccids = list(queryset.values_list('iccid', flat=True))
            
            # Obtener detalles y actualizar
            details = service.get_sim_details(iccids)
            updated = 0
            for sim_data in details:
                service._save_sim_to_db(sim_data)
                updated += 1
            
            self.message_user(
                request,
                f'{updated} SIM(s) sincronizada(s) exitosamente',
                level='SUCCESS'
            )
        except Exception as e:
            self.message_user(
                request,
                f'Error sincronizando SIMs: {str(e)}',
                level='ERROR'
            )
    sync_selected_sims.short_description = "⟳ Sincronizar SIMs seleccionadas"
    
    def sync_all_sims_action(self, request, queryset):
        # Sincronizar todas las SIMs desde la API
        try:
            service = WirelessLogicService()
            created, updated = service.sync_all_sims()
            
            self.message_user(
                request,
                f'Sincronización completada: {created} creadas, {updated} actualizadas',
                level='SUCCESS'
            )
        except Exception as e:
            self.message_user(
                request,
                f'Error en sincronización completa: {str(e)}',
                level='ERROR'
            )
    sync_all_sims_action.short_description = "⟳ Sincronizar TODAS las SIMs"


@admin.register(WirelessLogic_Usage)
class WirelessLogic_Usage_Admin(admin.ModelAdmin):
    class Meta:
        app_label = 'API READS'
    list_display = (
        'sim_link',
        'sim_iccid',
        'period_start',
        'period_end',
        'data_used_mb',
        'sms_sent',
        'sms_received',
        'voice_minutes',
        'total_cost',
        'currency',
        'last_read_time',
    )

    def last_read_time(self, obj):
        return obj.updated_at
    last_read_time.short_description = 'Last Read Time'

# (Other API reads admin classes and registrations follow...)
    list_filter = ('period_start', 'period_end', 'currency', 'sim__status')
    search_fields = ('sim__iccid', 'sim__msisdn')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'period_start'
    actions = ['sync_usage_action']
    
    fieldsets = (
        ('SIM y Periodo', {
            'fields': ('sim', 'period_start', 'period_end')
        }),
        ('Datos de Uso', {
            'fields': ('data_used_mb', 'sms_sent', 'sms_received', 'voice_minutes')
        }),
        ('Costos', {
            'fields': ('total_cost', 'currency')
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at')
        }),
        ('Datos Raw', {
            'fields': ('raw_data',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        # Optimizar query con select_related
        qs = super().get_queryset(request)
        return qs.select_related('sim')

    def sim_link(self, obj):
        # Enlaza a la ficha de la SIM
        url = reverse('admin:boreas_mediacion_wirelesslogic_sim_change', args=[obj.sim.id])
        label = obj.sim.msisdn or obj.sim.iccid
        return format_html('<a href="{}">{}</a>', url, label)
    sim_link.short_description = 'SIM'
    sim_link.admin_order_field = 'sim__msisdn'

    def sim_iccid(self, obj):
        # Muestra el ICCID de la SIM
        return obj.sim.iccid
    sim_iccid.short_description = 'ICCID'
    sim_iccid.admin_order_field = 'sim__iccid'

    def sync_usage_action(self, request, queryset):
        # Sincronizar uso de todas las SIMs
        try:
            service = WirelessLogicService()
            created = service.sync_sim_usage()
            self.message_user(
                request,
                f'Uso sincronizado: {created} registros creados/actualizados',
                level='SUCCESS'
            )
        except Exception as e:
            self.message_user(
                request,
                f'Error sincronizando uso: {str(e)}',
                level='ERROR'
            )
    sync_usage_action.short_description = "⟳ Sincronizar USO (todas las SIMs)"


# Sigfox admin
@admin.register(SigfoxDevice)
class SigfoxDeviceAdmin(admin.ModelAdmin):
    class Meta:
        app_label = 'API READS'
    list_display = ('device_id', 'firmware', 'last_seen', 'last_co2', 'last_temp', 'last_hum', 'last_read_time')

    def last_read_time(self, obj):
        latest = obj.readings.order_by('-timestamp').first()
        return latest.timestamp if latest else None
    last_read_time.short_description = 'Last Read Time'
    search_fields = ('device_id',)
    readonly_fields = ('created_at', 'updated_at')
    actions = ['create_test_reading', 'show_recent_readings']

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

        msg = '; '.join(summaries[:10])  # limitar longitud del mensaje
        self.message_user(request, msg, level=messages.INFO)
    show_recent_readings.short_description = "👀 Ver últimas lecturas"


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




