import json

import django_filters
from django.http import JsonResponse
from rest_framework import viewsets, permissions, generics

from .models import mqtt_msg, reported_measure
# from .mqtt import client as mqtt_client
from .serializers import mqtt_msgSerializer, reported_measureSerializer
from django_filters.rest_framework import DjangoFilterBackend
from django_filters.rest_framework import filters


# def publish_message(request):
#     # request_data = json.loads(request.body)
#     # rc, mid = mqtt_client.publish(request_data['topic'], request_data['msg'])
#     topic='django/mqtt'
#     msg='Hola desde Django'
#     request_data={"topic":topic,"msg":msg}
#     rc, mid = mqtt_client.publish(request_data['topic'], request_data['msg'])
#     # rc, mid = mqtt_client.publish(topic,msg)
#     return JsonResponse({'code': rc})

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