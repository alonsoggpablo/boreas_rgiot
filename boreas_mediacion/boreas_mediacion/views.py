import json
from datetime import datetime
import paho.mqtt.client as mqtt
import django_filters
from django.http import JsonResponse
from paho.mqtt.client import ssl
from rest_framework import viewsets, permissions, generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes, action
from django.utils import timezone
from django.shortcuts import render
from django.db.models import Max
from django.views.generic import ListView

from .models import mqtt_msg, reported_measure, MQTT_broker, MQTT_tx, WirelessLogic_SIM, WirelessLogic_Usage, SigfoxDevice, SigfoxReading, MQTT_device_family
# from .mqtt import client as mqtt_client
from .serializers import (mqtt_msgSerializer, reported_measureSerializer, MQTT_tx_serializer,
                          WirelessLogic_SIMSerializer, WirelessLogic_SIMListSerializer, 
                          WirelessLogic_UsageSerializer, SigfoxDeviceSerializer, SigfoxReadingSerializer)
from django_filters.rest_framework import DjangoFilterBackend
from django_filters.rest_framework import filters
from . import mqtt as mqtt_module
from .wirelesslogic_service import WirelessLogicService
from django.conf import settings
from rest_framework.authentication import BasicAuthentication
from rest_framework.permissions import IsAuthenticated

class mqtt_msgViewSet(viewsets.ModelViewSet):
    serializer_class = mqtt_msgSerializer
    permission_classes = [permissions.AllowAny]  # Permitir acceso público para testing
    queryset = mqtt_msg.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['device_id']

class mqtt_msgViewList(generics.ListAPIView):
    queryset = mqtt_msg.objects.all()
    serializer_class = mqtt_msgSerializer
    permission_classes = [permissions.AllowAny]  # Permitir acceso público para testing
    filter_backends=[DjangoFilterBackend]
    filterset_fields=['device_id']

class reported_measureViewList(generics.ListAPIView):
    queryset = reported_measure.objects.all()
    serializer_class = reported_measureSerializer
    permission_classes = [permissions.AllowAny]  # Permitir acceso público para testing
    filter_backends=[DjangoFilterBackend]
    filterset_fields=['device_id']

class PublishView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    allowed_methods = ['POST', 'GET']
    queryset=MQTT_tx.objects.all()
    serializer_class= MQTT_tx_serializer

    def post(self, request):
        mqtt_server = MQTT_broker.objects.filter(name='rgiot').values_list('server', flat=True)[0]
        mqtt_port = MQTT_broker.objects.filter(name='rgiot').values_list('port', flat=True)[0]
        mqtt_keepalive = MQTT_broker.objects.filter(name='rgiot').values_list('keepalive', flat=True)[0]
        mqtt_user = MQTT_broker.objects.filter(name='rgiot').values_list('user', flat=True)[0]
        mqtt_password = MQTT_broker.objects.filter(name='rgiot').values_list('password', flat=True)[0]

        MQTT_SERVER = mqtt_server
        MQTT_PORT = mqtt_port
        MQTT_KEEPALIVE = mqtt_keepalive
        MQTT_USER = mqtt_user
        MQTT_PASSWORD = mqtt_password

        data = request.data

        client = mqtt.Client()
        client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
        client.tls_set(certfile=None,
                       keyfile=None, cert_reqs=ssl.CERT_NONE,
                       tls_version=ssl.PROTOCOL_TLSv1_2, ciphers=None)

        def on_connect(client, userdata, flags, rc):

            if rc == 0:
                print('Connected successfully')
                client.publish(self.request.data['topic'], self.request.data['payload'])
            else:
                print('Bad connection. Code:', rc)
            client.disconnect()

        client.on_connect=on_connect

        client.connect(
            host=MQTT_SERVER,
            port=MQTT_PORT,
            keepalive=MQTT_KEEPALIVE
        )


        client.loop_start()
        return Response({'received data': request.data})

    def get(self, request):
        # Logic for handling GET request
        return Response({"message": "GET request handled"})


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def mqtt_control(request):
    """Control MQTT client: start, stop, or get status"""
    action = request.data.get('action', '')
    
    if action == 'start':
        result = mqtt_module.start_mqtt_client()
    elif action == 'stop':
        result = mqtt_module.stop_mqtt_client()
    elif action == 'status':
        result = mqtt_module.get_mqtt_status()
    else:
        result = {"status": "error", "message": "Invalid action. Use 'start', 'stop', or 'status'"}
    
    return Response(result)


# WirelessLogic ViewSets
class WirelessLogic_SIMViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar SIMs de WirelessLogic
    
    Endpoints:
    - list: GET /api/wirelesslogic/sims/
    - retrieve: GET /api/wirelesslogic/sims/{id}/
    - sync_all: POST /api/wirelesslogic/sims/sync_all/
    - sync_usage: POST /api/wirelesslogic/sims/sync_usage/
    """
    queryset = WirelessLogic_SIM.objects.all()
    permission_classes = [permissions.AllowAny]  # Cambiar a IsAuthenticated en producción
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['iccid', 'msisdn', 'status', 'network']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return WirelessLogic_SIMListSerializer
        return WirelessLogic_SIMSerializer
    
    @action(detail=False, methods=['post'])
    def sync_all(self, request):
        """
        Sincroniza todas las SIMs desde la API de WirelessLogic
        
        POST /api/wirelesslogic/sims/sync_all/
        """
        try:
            service = WirelessLogicService()
            created, updated = service.sync_all_sims()
            
            return Response({
                'status': 'success',
                'message': f'Sincronización completada',
                'sims_created': created,
                'sims_updated': updated,
                'total_sims': WirelessLogic_SIM.objects.count()
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def sync_usage(self, request):
        """
        Sincroniza datos de uso de SIMs
        
        POST /api/wirelesslogic/sims/sync_usage/
        Body (opcional): {"days_back": 30}
        """
        try:
            days_back = request.data.get('days_back', 30)
            service = WirelessLogicService()
            usage_count = service.sync_sim_usage(days_back=days_back)
            
            return Response({
                'status': 'success',
                'message': f'Sincronización de uso completada',
                'usage_records_created': usage_count,
                'days_back': days_back
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'])
    def usage_history(self, request, pk=None):
        """
        Obtiene historial de uso de una SIM específica
        
        GET /api/wirelesslogic/sims/{id}/usage_history/
        """
        sim = self.get_object()
        usage_records = sim.usage_records.all()
        serializer = WirelessLogic_UsageSerializer(usage_records, many=True)
        return Response(serializer.data)


class WirelessLogic_UsageViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet de solo lectura para datos de uso de SIMs
    
    Endpoints:
    - list: GET /api/wirelesslogic/usage/
    - retrieve: GET /api/wirelesslogic/usage/{id}/
    """
    queryset = WirelessLogic_Usage.objects.all()
    serializer_class = WirelessLogic_UsageSerializer
    permission_classes = [permissions.AllowAny]  # Cambiar a IsAuthenticated en producción
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['sim__iccid', 'period_start', 'period_end']


# Sigfox ViewSets
class SigfoxDeviceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SigfoxDevice.objects.all()
    serializer_class = SigfoxDeviceSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['device_id']


class SigfoxReadingViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SigfoxReading.objects.all()
    serializer_class = SigfoxReadingSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['device__device_id', 'timestamp']


class SigfoxCallbackView(APIView):
    """Recibe callbacks Sigfox (equivalente al flujo Node-RED /sigfox/gas)."""
    # Ignoramos autenticaciones globales; manejamos Basic auth personalizada dentro del view
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def _check_basic_auth(self, request):
        expected = getattr(settings, 'SIGFOX_BASIC_AUTH', None)
        if not expected:
            # valor por defecto rgiot:rgiot codificado
            expected = 'Basic cmdpb3Q6cmdpb3Q='
        received = request.META.get('HTTP_AUTHORIZATION', '')
        return received.strip() == expected

    def post(self, request):
        if not self._check_basic_auth(request):
            return Response({'status': 'error', 'message': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)

        payload = request.data if isinstance(request.data, dict) else {}
        device_id = payload.get('device')
        data_hex = payload.get('data', '') or ''
        ts = payload.get('timestamp')

        if not device_id or not data_hex:
            return Response({'status': 'error', 'message': 'device y data son obligatorios'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            timestamp = datetime.fromtimestamp(int(ts), tz=timezone.utc) if ts is not None else timezone.now()
        except Exception:
            timestamp = timezone.now()

        # Parseo similar al flow Node-RED
        fw = data_hex[0:1] or None
        temp = None
        hum = None
        co2 = None
        base = None
        try:
            temp = round((int(data_hex[2:6], 16) / 10) - 40, 2)
            hum = int(data_hex[6:8], 16)
            co2 = int(data_hex[8:12], 16)
            base = int(data_hex[12:14], 16)
        except Exception:
            pass

        device, _ = SigfoxDevice.objects.get_or_create(device_id=device_id)
        device.firmware = fw or device.firmware
        device.last_seen = timestamp
        device.last_payload = payload
        device.last_co2 = co2
        device.last_temp = temp
        device.last_hum = hum
        device.last_base = base
        device.save()

        SigfoxReading.objects.create(
            device=device,
            timestamp=timestamp,
            firmware=fw,
            co2=co2,
            temp=temp,
            hum=hum,
            base=base,
            raw_data=payload
        )


# Web Views for Dashboard

def family_last_messages(request):
    """
    View to display the last message received for each MQTT device family.
    Supports filtering by family name and device_id.
    Shows ALL families, including those without messages.
    """
    # Get all families with their last message
    families = MQTT_device_family.objects.all()
    
    family_data = []
    for family in families:
        # Get the last message for this family
        last_msg = mqtt_msg.objects.filter(device_family=family).order_by('-report_time').first()
        
        # Include family even if no messages
        family_data.append({
            'family': family,
            'last_message': last_msg,
            'device_id': last_msg.device_id if last_msg else 'N/A',
            'report_time': last_msg.report_time if last_msg else None,
            'measures': last_msg.measures if last_msg else 'No data',
        })
    
    # Apply filter if provided
    family_filter = request.GET.get('family_name', '').strip()

    if family_filter:
        family_data = [f for f in family_data if family_filter.lower() == f['family'].name.lower()]
    
    # Sort alphabetically by family name
    family_data.sort(key=lambda x: x['family'].name.lower())
    
    # Calculate total messages
    total_messages = mqtt_msg.objects.count()
    
    context = {
        'family_data': family_data,
        'families': MQTT_device_family.objects.all().values_list('name', flat=True).distinct(),
        'family_filter': family_filter,
        'total_messages': total_messages,
        'now': timezone.now(),
    }
    
    return render(request, 'family_messages.html', context)
