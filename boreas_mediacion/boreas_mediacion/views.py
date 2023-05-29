import json

import django_filters
from django.http import JsonResponse
from paho.mqtt.client import ssl
from rest_framework import viewsets, permissions, generics
from rest_framework.response import Response
from rest_framework.views import APIView
import paho.mqtt.client as mqtt

from .models import mqtt_msg, reported_measure, MQTT_broker
# from .mqtt import client as mqtt_client
from .serializers import mqtt_msgSerializer, reported_measureSerializer
from django_filters.rest_framework import DjangoFilterBackend
from django_filters.rest_framework import filters


class mqtt_msgViewSet(viewsets.ModelViewSet):
    serializer_class = mqtt_msgSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = mqtt_msg.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['device_id']


class mqtt_msgViewList(generics.ListAPIView):
    queryset = mqtt_msg.objects.all()
    serializer_class = mqtt_msgSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends=[DjangoFilterBackend]
    filterset_fields=['device_id']

class reported_measureViewList(generics.ListAPIView):
    queryset = reported_measure.objects.all()
    serializer_class = reported_measureSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends=[DjangoFilterBackend]
    filterset_fields=['device_id']

import paho.mqtt.client as mqtt



class PublishView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    allowed_methods = ['POST', 'GET']

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