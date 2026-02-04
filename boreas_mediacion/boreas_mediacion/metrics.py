from prometheus_client import Counter, Histogram, Gauge, generate_latest
from prometheus_client import CollectorRegistry
from .models import MQTT_device_family, MQTT_topic, TopicMessageTimeout, SigfoxDevice, SigfoxReading, WirelessLogic_SIM, DatadisSupply, DeviceMonitoring, AemetStation
from django.utils import timezone
from django.http import HttpResponse


registry = CollectorRegistry()
REQUEST_COUNT = Counter('django_http_requests_total', 'Total HTTP requests', registry=registry)
REQUEST_LATENCY = Histogram('django_http_request_latency_seconds', 'Request latency', registry=registry)
FAMILIES_NO_MSG = Gauge('families_no_message_count', 'Number of device families with no messages in the last hour', registry=registry)
FAMILY_TIMEOUT = Gauge('family_timeout', 'Timeout for each device family (1=timeout, 0=ok)', ['family'], registry=registry)
MQTT_TOPIC_TIMEOUT = Gauge('mqtt_topic_timeout', 'Timeout for MQTT topic (1=timeout, 0=ok)', ['topic'], registry=registry)
MQTT_TOPIC_MONITORED_TIMEOUT = Gauge('mqtt_topic_monitored_timeout', 'Timeout for monitored MQTT topic (1=timeout, 0=ok)', ['topic'], registry=registry)
SIGFOX_DEVICE_TIMEOUT = Gauge('sigfox_device_timeout', 'Timeout for Sigfox device (1=timeout, 0=ok)', ['device_id'], registry=registry)
WIRELESSLOGIC_SIM_TIMEOUT = Gauge('wirelesslogic_sim_timeout', 'Timeout for WirelessLogic SIM (1=timeout, 0=ok)', ['iccid'], registry=registry)
DATADIS_SUPPLY_TIMEOUT = Gauge('datadis_supply_timeout', 'Timeout for Datadis supply (1=timeout, 0=ok)', ['cups'], registry=registry)
AEMET_STATION_TIMEOUT = Gauge('aemet_station_timeout', 'Timeout for AEMET station (1=timeout, 0=ok)', ['station_id'], registry=registry)

class PrometheusMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    def __call__(self, request):
        REQUEST_COUNT.inc()
        with REQUEST_LATENCY.time():
            response = self.get_response(request)
        return response

def metrics_view(request):
    # Families timeout
    two_hours_ago = timezone.now() - timezone.timedelta(hours=2)
    families = MQTT_device_family.objects.all()
    for family in families:
        last_msg = None  # mqtt_msg removed
        if not last_msg:
            FAMILY_TIMEOUT.labels(family=family.name).set(1)
        else:
            FAMILY_TIMEOUT.labels(family=family.name).set(0)

    # MQTT topic timeouts (active only)
    active_topics = MQTT_topic.objects.filter(active=True)
    for topic in active_topics:
        timeout_cfg = TopicMessageTimeout.objects.filter(topic=topic.topic, active=True).first()
        if timeout_cfg:
            last_time = timeout_cfg.last_message_time
            timeout_minutes = timeout_cfg.timeout_minutes
            if not last_time or (timezone.now() - last_time).total_seconds() > timeout_minutes * 60:
                MQTT_TOPIC_TIMEOUT.labels(topic=topic.topic).set(1)
            else:
                MQTT_TOPIC_TIMEOUT.labels(topic=topic.topic).set(0)

    # Monitored MQTT topic timeouts (active only, check DeviceMonitoring table)
    active_topics = MQTT_topic.objects.filter(active=True)
    for topic in active_topics:
        timeout_cfg = TopicMessageTimeout.objects.filter(topic=topic.topic, active=True).first()
        if timeout_cfg:
            last_time = timeout_cfg.last_message_time
            timeout_minutes = timeout_cfg.timeout_minutes
            
            # Check if this topic's devices are being monitored
            # Extract family name from topic (first segment) and check if any devices in that family are monitored
            family_name = topic.topic.split('/')[0] if '/' in topic.topic else topic.topic
            monitored_count = DeviceMonitoring.objects.filter(
                source=family_name.lower(),
                monitored=True
            ).count()
            
            if monitored_count > 0:  # Only alert if there are monitored devices in this family
                if not last_time or (timezone.now() - last_time).total_seconds() > timeout_minutes * 60:
                    MQTT_TOPIC_MONITORED_TIMEOUT.labels(topic=topic.topic).set(1)
                else:
                    MQTT_TOPIC_MONITORED_TIMEOUT.labels(topic=topic.topic).set(0)

    # API timeouts: Sigfox, WirelessLogic, Datadis
    # Sigfox: device not seen in last 2 hours
    for device in SigfoxDevice.objects.all():
        last_seen = device.last_seen
        if not last_seen or (timezone.now() - last_seen).total_seconds() > 7200:
            SIGFOX_DEVICE_TIMEOUT.labels(device_id=device.device_id).set(1)
        else:
            SIGFOX_DEVICE_TIMEOUT.labels(device_id=device.device_id).set(0)

    for sim in WirelessLogic_SIM.objects.all():
        last_sync = sim.last_sync
        if not last_sync or (timezone.now() - last_sync).total_seconds() > 7200:
            WIRELESSLOGIC_SIM_TIMEOUT.labels(iccid=sim.iccid).set(1)
        else:
            WIRELESSLOGIC_SIM_TIMEOUT.labels(iccid=sim.iccid).set(0)

    for supply in DatadisSupply.objects.filter(active=True):
        last_sync = supply.raw_data.get('last_sync')
        # Increase timeout to 2 hours (7200 seconds) to account for UTC/UTC+1 offset
        if not last_sync or (timezone.now() - timezone.datetime.fromisoformat(last_sync)).total_seconds() > 7200:
            DATADIS_SUPPLY_TIMEOUT.labels(cups=supply.cups).set(1)
        else:
            DATADIS_SUPPLY_TIMEOUT.labels(cups=supply.cups).set(0)

    # AEMET station timeouts: stations not updated in last 2 hours
    for station in AemetStation.objects.filter(active=True):
        last_update = station.updated_at
        if not last_update or (timezone.now() - last_update).total_seconds() > 7200:
            AEMET_STATION_TIMEOUT.labels(station_id=station.station_id).set(1)
        else:
            AEMET_STATION_TIMEOUT.labels(station_id=station.station_id).set(0)

    return HttpResponse(generate_latest(registry), content_type='text/plain')
