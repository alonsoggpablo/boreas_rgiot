from django.contrib import admin
from .models import mqtt_msg, MQTT_device_family, MQTT_broker, MQTT_feed, sensor_command, sensor_actuacion, router_get, \
    router_parameter
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


#register MQTT_feed
class MQTT_feed_Admin(admin.ModelAdmin):
   list_display = ('name','description','topic')
   list_filter = ('name','description','topic')
   search_fields = ('name','description','topic')
admin.site.register(MQTT_feed,MQTT_feed_Admin)

#register sensor command
class sensor_command_Admin(admin.ModelAdmin):
   list_display = ('device_id','circuit','actuacion')
   list_filter = ('device_id','circuit','actuacion')
   search_fields = ('device_id','circuit','actuacion')
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

admin.site.register(router_get,router_get_Admin)

#register router_parameter
class router_parameter_Admin(admin.ModelAdmin):
    list_display = ('parameter','description')
    list_filter = ('parameter','description')
    search_fields = ('parameter','description')
admin.site.register(router_parameter,router_parameter_Admin)



