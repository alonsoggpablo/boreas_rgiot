from .models import mqtt_msg
from rest_framework import serializers

class mqtt_msgSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = mqtt_msg
        fields = ('report_time', 'device', 'measures')
