from .models import reported_measure, MQTT_tx, sensor_command, WirelessLogic_SIM, WirelessLogic_Usage, SigfoxDevice, SigfoxReading
from rest_framework import serializers



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


# WirelessLogic Serializers
class WirelessLogic_UsageSerializer(serializers.ModelSerializer):
    class Meta:
        model = WirelessLogic_Usage
        fields = ('id', 'period_start', 'period_end', 'data_used_mb', 'sms_sent', 
                 'sms_received', 'voice_minutes', 'total_cost', 'currency', 'raw_data', 
                 'created_at', 'updated_at')
        read_only_fields = ('created_at', 'updated_at')


class WirelessLogic_SIMSerializer(serializers.ModelSerializer):
    usage_records = WirelessLogic_UsageSerializer(many=True, read_only=True)
    latest_usage = serializers.SerializerMethodField()
    
    class Meta:
        model = WirelessLogic_SIM
        fields = ('id', 'iccid', 'msisdn', 'imsi', 'status', 'activation_date', 
                 'tariff_name', 'account_name', 'network', 'roaming_network', 
                 'raw_data', 'last_sync', 'created_at', 'updated_at', 
                 'usage_records', 'latest_usage')
        read_only_fields = ('last_sync', 'created_at', 'updated_at')
    
    def get_latest_usage(self, obj):
        latest = obj.usage_records.first()
        if latest:
            return WirelessLogic_UsageSerializer(latest).data
        return None


class WirelessLogic_SIMListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listados"""
    latest_data_usage = serializers.SerializerMethodField()
    
    class Meta:
        model = WirelessLogic_SIM
        fields = ('id', 'iccid', 'msisdn', 'status', 'tariff_name', 
                 'network', 'last_sync', 'latest_data_usage')
    
    def get_latest_data_usage(self, obj):
        latest = obj.usage_records.first()
        return latest.data_used_mb if latest else 0


# Sigfox serializers
class SigfoxReadingSerializer(serializers.ModelSerializer):
    device_id = serializers.CharField(source='device.device_id', read_only=True)

    class Meta:
        model = SigfoxReading
        fields = (
            'id', 'device_id', 'timestamp', 'firmware', 'co2', 'temp', 'hum', 'base', 'raw_data',
            'created_at', 'updated_at'
        )
        read_only_fields = ('created_at', 'updated_at')


class SigfoxDeviceSerializer(serializers.ModelSerializer):
    latest_reading = serializers.SerializerMethodField()

    class Meta:
        model = SigfoxDevice
        fields = (
            'id', 'device_id', 'firmware', 'last_seen', 'last_co2', 'last_temp', 'last_hum', 'last_base',
            'last_payload', 'created_at', 'updated_at', 'latest_reading'
        )
        read_only_fields = ('created_at', 'updated_at')

    def get_latest_reading(self, obj):
        latest = obj.readings.first()
        return SigfoxReadingSerializer(latest).data if latest else None
