from django.contrib import admin
from .models import mqtt_msg, MQTT_device_family, MQTT_broker
from .models import MQTT_topic

class MQTT_MSG_Admin(admin.ModelAdmin):
    list_display = ('device','measures','report_time')
    list_filter = ('device',
                   )
admin.site.register(mqtt_msg,MQTT_MSG_Admin)

# Register your models here.
#register MQTT_topic
class MQTT_topic_Admin(admin.ModelAdmin):
    list_display = ('topic','active','ro_rw','description','family','broker')
    list_filter = ('active','ro_rw','family','broker')
    search_fields = ('topic','description','family','broker')
admin.site.register(MQTT_topic,MQTT_topic_Admin)

class MQTT_device_family_Admin(admin.ModelAdmin):
    list_display = ('name',)
    list_filter = ('name',)
    search_fields = ('name',)
admin.site.register(MQTT_device_family,MQTT_device_family_Admin)

class MQTT_broker_Admin(admin.ModelAdmin):
    list_display = ('name','server','user','password','port','keepalive','description','active')
    list_filter = ('active',)
    search_fields = ('name','server','description')
admin.site.register(MQTT_broker,MQTT_broker_Admin)


