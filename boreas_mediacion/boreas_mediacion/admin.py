from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.http import HttpResponseRedirect
from .models import mqtt_msg, MQTT_device_family, MQTT_broker, MQTT_feed, sensor_command, sensor_actuacion, router_get, \
    router_parameter, reported_measure
from .models import MQTT_topic
from . import mqtt as mqtt_module

class MQTT_MSG_Admin(admin.ModelAdmin):
    list_display = ('device_id','device','measures','feed','device_family','report_time')
    list_filter = ('feed','report_time','device_id','device_family')
    search_fields = ('device_id','device','measures','report_time')
admin.site.register(mqtt_msg,MQTT_MSG_Admin)

# Register your models here.
#register MQTT_topic
class MQTT_topic_Admin(admin.ModelAdmin):
    list_display = ('topic','active','ro_rw','description','family','broker')
    list_filter = ('active','ro_rw','family','broker')
    search_fields = ('topic','description','family','broker')
    actions = ['activate_topics', 'deactivate_topics']
    
    def activate_topics(self, request, queryset):
        """Activate selected MQTT topics"""
        updated = queryset.update(active=True)
        self.message_user(request, f'{updated} topic(s) activated successfully')
    activate_topics.short_description = "✓ Activate selected topics"
    
    def deactivate_topics(self, request, queryset):
        """Deactivate selected MQTT topics"""
        updated = queryset.update(active=False)
        self.message_user(request, f'{updated} topic(s) deactivated successfully')
    deactivate_topics.short_description = "✗ Deactivate selected topics"

admin.site.register(MQTT_topic,MQTT_topic_Admin)

class MQTT_device_family_Admin(admin.ModelAdmin):
    list_display = ('name',)
    list_filter = ('name',)
    search_fields = ('name',)
admin.site.register(MQTT_device_family,MQTT_device_family_Admin)

class MQTT_broker_Admin(admin.ModelAdmin):
    list_display = ('name','server','user','password','port','keepalive','description','active','mqtt_status_display')
    list_filter = ('active',)
    search_fields = ('name','server','description')
    actions = ['start_mqtt', 'stop_mqtt']
    
    def mqtt_status_display(self, obj):
        """Display current MQTT client status"""
        status = mqtt_module.get_mqtt_status()
        if status['running']:
            color = 'green'
            text = '● Running'
        else:
            color = 'red'
            text = '● Stopped'
        return format_html('<span style="color: {};">{}</span>', color, text)
    mqtt_status_display.short_description = 'MQTT Status'
    
    def start_mqtt(self, request, queryset):
        """Start MQTT client"""
        try:
            result = mqtt_module.start_mqtt_client()
            if result['status'] == 'success':
                self.message_user(request, result['message'], level='SUCCESS')
            elif result['status'] == 'already_running':
                self.message_user(request, result['message'], level='WARNING')
            else:
                self.message_user(request, result['message'], level='ERROR')
        except Exception as e:
            self.message_user(request, f'Error starting MQTT client: {str(e)}', level='ERROR')
    start_mqtt.short_description = "▶ Start MQTT Client"
    
    def stop_mqtt(self, request, queryset):
        """Stop MQTT client"""
        try:
            result = mqtt_module.stop_mqtt_client()
            if result['status'] == 'success':
                self.message_user(request, result['message'], level='SUCCESS')
            elif result['status'] == 'already_stopped':
                self.message_user(request, result['message'], level='WARNING')
            else:
                self.message_user(request, result['message'], level='ERROR')
        except Exception as e:
            self.message_user(request, f'Error stopping MQTT client: {str(e)}', level='ERROR')
    stop_mqtt.short_description = "■ Stop MQTT Client"

admin.site.register(MQTT_broker,MQTT_broker_Admin)


#register MQTT_feed
class MQTT_feed_Admin(admin.ModelAdmin):
   list_display = ('name','description','topic','get_family')
   list_filter = ('topic__family','name','description')
   search_fields = ('name','description','topic__topic')
   
   def get_family(self, obj):
       """Display the family of the feed's topic"""
       if obj.topic and obj.topic.family:
           return obj.topic.family.name
       return '-'
   get_family.short_description = 'Family'

admin.site.register(MQTT_feed,MQTT_feed_Admin)

#register sensor command
class sensor_command_Admin(admin.ModelAdmin):
   list_display = ('device_id','circuit','actuacion')
   list_filter = ('device_id','circuit','actuacion')
   search_fields = ('device_id','circuit','actuacion')

   def formfield_for_foreignkey(self, db_field, request, **kwargs):
       if db_field.name == 'device_id':
           kwargs['queryset'] = mqtt_msg.objects.order_by('device_id').distinct('device_id')
       return super().formfield_for_foreignkey(db_field, request, **kwargs)

admin.site.register(sensor_command,sensor_command_Admin)

#register sensor actuacion
class sensor_actuacion_Admin(admin.ModelAdmin):
    list_display = ('tipo','command','description')
    list_filter = ('tipo','command','description')
    search_fields = ('tipo','command','description')
admin.site.register(sensor_actuacion,sensor_actuacion_Admin)

#register router_get
class router_get_Admin(admin.ModelAdmin):
    list_display = ('device_id','parameter')
    list_filter = ('device_id','parameter')
    search_fields = ('device_id','parameter')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'device_id':
            kwargs['queryset'] = mqtt_msg.objects.order_by('device_id').distinct('device_id')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

admin.site.register(router_get,router_get_Admin)

#register router_parameter
class router_parameter_Admin(admin.ModelAdmin):
    list_display = ('parameter','description')
    list_filter = ('parameter','description')
    search_fields = ('parameter','description')
admin.site.register(router_parameter,router_parameter_Admin)

#register reported_measure
class reported_measure_Admin(admin.ModelAdmin):
    list_display = ('feed','device_id','measures','report_time')
    list_filter = ('feed','report_time','device_id')
    search_fields = ('device_id','measures','report_time')
admin.site.register(reported_measure,reported_measure_Admin)



