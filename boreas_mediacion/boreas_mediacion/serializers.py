from .models import mqtt_msg, reported_measure, MQTT_tx, sensor_command
from rest_framework import serializers

class mqtt_msgSerializer(serializers.ModelSerializer):
    class Meta:
        model = mqtt_msg
        fields = ('id', 'report_time', 'device', 'device_id', 'measures', 'feed')

class reported_measureSerializer(serializers.ModelSerializer):
    class Meta:
        model = reported_measure
        fields = ('id', 'report_time', 'device', 'device_id', 'measures', 'feed')


class MQTT_tx_serializer(serializers.ModelSerializer):
    class Meta:
        model = MQTT_tx
        fields = ('id', 'topic', 'payload')

class sensor_command_serializer(serializers.ModelSerializer):
    class Meta:
        model = sensor_command
        fields = ('id', 'device_id', 'circuit','actuacion')
