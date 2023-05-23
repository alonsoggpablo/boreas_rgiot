from django.db import models

class mqtt_msg(models.Model):
    report_time=models.DateTimeField(auto_now=True)
    device=models.JSONField(unique=True)
    device_id=models.CharField(max_length=100)
    measures=models.JSONField()
    feed=models.CharField(max_length=100)

class reported_measure(models.Model):
    report_time=models.DateTimeField(auto_now=True)
    device=models.JSONField()
    device_id=models.CharField(max_length=100)
    measures=models.JSONField()
    feed=models.CharField(max_length=100)


class MQTT_device_family(models.Model):
    name=models.CharField(max_length=100)
    def __str__(self):
        return self.name

class MQTT_broker(models.Model):
    name=models.CharField(max_length=100)
    server=models.CharField(max_length=100)
    port=models.IntegerField(default=1883)
    keepalive=models.IntegerField(default=60)
    description=models.CharField(max_length=100)
    active=models.BooleanField(default=False)
    user = models.CharField(max_length=100)
    password = models.CharField(max_length=100)
    def __str__(self):
        return self.name

class MQTT_topic(models.Model):
    broker=models.ForeignKey(MQTT_broker,on_delete=models.CASCADE)
    family=models.ForeignKey(MQTT_device_family,on_delete=models.CASCADE)
    topic=models.CharField(max_length=100)
    qos=models.IntegerField(default=0)
    description=models.CharField(max_length=100)
    active=models.BooleanField(default=False)
    ro_rw=models.CharField(max_length=2,default='ro')
    def __str__(self):
        return self.description



