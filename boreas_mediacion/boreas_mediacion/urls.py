"""
URL configuration for boreas_mediacion project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from boreas_bot import views as boreas_bot_views
from django.views.generic import RedirectView
from rest_framework import routers

from . import views
from .views import PublishView, DeviceLastReadsView, DashboardIndexView

router = routers.DefaultRouter()
router.register(r'wirelesslogic/sims', views.WirelessLogic_SIMViewSet, basename='wirelesslogic-sim')
router.register(r'wirelesslogic/usage', views.WirelessLogic_UsageViewSet, basename='wirelesslogic-usage')
router.register(r'sigfox/devices', views.SigfoxDeviceViewSet, basename='sigfox-device')
router.register(r'sigfox/readings', views.SigfoxReadingViewSet, basename='sigfox-reading')
router.register(r'anomalies', views.DetectedAnomalyViewSet, basename='anomaly')
router.register(r'device-types', views.DeviceTypeMappingViewSet, basename='device-type')
router.register(r'external-devices', views.ExternalDeviceMappingViewSet, basename='external-device')


urlpatterns = [
    path('', RedirectView.as_view(url='/dashboard/', permanent=False)),
    path('dashboard/', DashboardIndexView.as_view(), name='dashboard_index'),
    path('dashboard/family-messages/', views.family_last_messages, name='family_messages'),
    path('dashboard/device-last-reads/', DeviceLastReadsView.as_view(), name='device_last_reads'),
    path('accounts/', include('django.contrib.auth.urls')),  # Django login/logout
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('admin/', admin.site.urls),
    path('api/mqtt/active-topics/', views.active_mqtt_topics, name='active_mqtt_topics'),
    path('metrics/', __import__('boreas_mediacion.metrics').metrics.metrics_view),
    path('external-devices/', boreas_bot_views.devices_external_list, name='external_devices'),
    path('api/publish/', PublishView.as_view(), name='publish'),
    path('api/mqtt-control/', views.mqtt_control, name='mqtt_control'),
    path('api/sigfox', views.SigfoxCallbackView.as_view(), name='sigfox'),
    path('api/sigfox/gas', views.SigfoxCallbackView.as_view(), name='sigfox_gas'),
    re_path(r'^api/reported_measure-list/$', views.reported_measureViewList.as_view()),
    path('boreas-bot/devices/', boreas_bot_views.list_devices_tables, name='boreas_bot_devices'),
    path('api/upload-mockup-file/', boreas_bot_views.upload_mockup_file, name='upload_mockup_file'),
]

