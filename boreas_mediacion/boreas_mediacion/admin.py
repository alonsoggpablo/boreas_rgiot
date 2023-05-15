from django.contrib import admin
from .models import mqtt_msg

class MQTT_MSG_Admin(admin.ModelAdmin):
    list_display = ('device','measures','report_time')
    list_filter = ('device',
                   )
admin.site.register(mqtt_msg,MQTT_MSG_Admin)