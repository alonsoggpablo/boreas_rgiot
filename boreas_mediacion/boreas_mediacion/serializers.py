from .models import mqtt_msg, reported_measure, MQTT_tx, sensor_command
from rest_framework import serializers

class mqtt_msgSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = mqtt_msg
        fields = ('report_time', 'device', 'measures')

class reported_measureSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = reported_measure
        fields = ('report_time', 'device', 'measures')


class MQTT_tx_serializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = MQTT_tx
        fields = ('topic', 'payload')

class sensor_command_serializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = sensor_command
        fields = ('device_id', 'circuit','actuacion')

