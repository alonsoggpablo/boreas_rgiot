from .models import mqtt_msg, reported_measure
from rest_framework import serializers

class mqtt_msgSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = mqtt_msg
        fields = ('report_time', 'device', 'measures')

class reported_measureSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = reported_measure
        fields = ('report_time', 'device', 'measures')
