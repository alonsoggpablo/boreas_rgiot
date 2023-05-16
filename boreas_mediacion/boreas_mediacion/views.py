import json

from django.http import JsonResponse
from rest_framework import viewsets, permissions, generics

from .models import mqtt_msg
# from .mqtt import client as mqtt_client
from .serializers import mqtt_msgSerializer
from django_filters.rest_framework import DjangoFilterBackend


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

class mqtt_msgViewList(generics.ListAPIView):
    queryset = mqtt_msg.objects.all()
    serializer_class = mqtt_msgSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends=[DjangoFilterBackend]
    filter_fields=['id']
