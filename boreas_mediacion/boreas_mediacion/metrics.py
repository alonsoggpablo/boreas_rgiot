from prometheus_client import Counter, Histogram, Gauge, generate_latest
from prometheus_client import CollectorRegistry
from .models import MQTT_device_family, mqtt_msg, MQTT_topic, TopicMessageTimeout, SigfoxDevice, SigfoxReading, WirelessLogic_SIM, DatadisSupply
from django.utils import timezone
from django.http import HttpResponse


registry = CollectorRegistry()
REQUEST_COUNT = Counter('django_http_requests_total', 'Total HTTP requests', registry=registry)
REQUEST_LATENCY = Histogram('django_http_request_latency_seconds', 'Request latency', registry=registry)
FAMILIES_NO_MSG = Gauge('families_no_message_count', 'Number of device families with no messages in the last hour', registry=registry)
FAMILY_TIMEOUT = Gauge('family_timeout', 'Timeout for each device family (1=timeout, 0=ok)', ['family'], registry=registry)
MQTT_TOPIC_TIMEOUT = Gauge('mqtt_topic_timeout', 'Timeout for MQTT topic (1=timeout, 0=ok)', ['topic'], registry=registry)
SIGFOX_DEVICE_TIMEOUT = Gauge('sigfox_device_timeout', 'Timeout for Sigfox device (1=timeout, 0=ok)', ['device_id'], registry=registry)
WIRELESSLOGIC_SIM_TIMEOUT = Gauge('wirelesslogic_sim_timeout', 'Timeout for WirelessLogic SIM (1=timeout, 0=ok)', ['iccid'], registry=registry)
DATADIS_SUPPLY_TIMEOUT = Gauge('datadis_supply_timeout', 'Timeout for Datadis supply (1=timeout, 0=ok)', ['cups'], registry=registry)

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
    one_hour_ago = timezone.now() - timezone.timedelta(hours=1)
    families = MQTT_device_family.objects.all()
    for family in families:
        last_msg = mqtt_msg.objects.filter(device_family=family, report_time__gte=one_hour_ago).order_by('-report_time').first()
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

    # API timeouts: Sigfox, WirelessLogic, Datadis
    # Sigfox: device not seen in last hour
    for device in SigfoxDevice.objects.all():
        last_seen = device.last_seen
        if not last_seen or (timezone.now() - last_seen).total_seconds() > 3600:
            SIGFOX_DEVICE_TIMEOUT.labels(device_id=device.device_id).set(1)
        else:
            SIGFOX_DEVICE_TIMEOUT.labels(device_id=device.device_id).set(0)

    for sim in WirelessLogic_SIM.objects.all():
        last_sync = sim.last_sync
        if not last_sync or (timezone.now() - last_sync).total_seconds() > 3600:
            WIRELESSLOGIC_SIM_TIMEOUT.labels(iccid=sim.iccid).set(1)
        else:
            WIRELESSLOGIC_SIM_TIMEOUT.labels(iccid=sim.iccid).set(0)

    for supply in DatadisSupply.objects.filter(active=True):
        last_sync = supply.raw_data.get('last_sync')
        if not last_sync or (timezone.now() - timezone.datetime.fromisoformat(last_sync)).total_seconds() > 3600:
            DATADIS_SUPPLY_TIMEOUT.labels(cups=supply.cups).set(1)
        else:
            DATADIS_SUPPLY_TIMEOUT.labels(cups=supply.cups).set(0)

    return HttpResponse(generate_latest(registry), content_type='text/plain')
