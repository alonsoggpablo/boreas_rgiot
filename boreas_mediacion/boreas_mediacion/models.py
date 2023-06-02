from django.db import models
# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from . import mqtt


class mqtt_msg(models.Model):
    report_time=models.DateTimeField(auto_now=True)
    device=models.JSONField(unique=True)
    device_id=models.CharField(max_length=100)
    measures=models.JSONField()
    feed=models.CharField(max_length=100)

    class Meta:
        ordering = ['device_id']
    def __str__(self):
        return self.device_id

class reported_measure(models.Model):
    report_time=models.DateTimeField(auto_now=True)
    device=models.JSONField()
    device_id=models.CharField(max_length=100)
    measures=models.JSONField()
    feed=models.CharField(max_length=100)
    def __str__(self):
        return self.device_id


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
        return self.topic

class MQTT_tx(models.Model):
    topic=models.CharField(max_length=100)
    payload=models.CharField(max_length=1000)

    def __str__(self):
        return self.topic.topic
class MQTT_feed(models.Model):
    name=models.CharField(max_length=100)
    description=models.CharField(max_length=100)
    topic=models.ForeignKey(MQTT_topic,on_delete=models.CASCADE)
    def __str__(self):
        return self.name

class sensor_actuacion(models.Model):
    tipo=models.CharField(max_length=100)
    command=models.CharField(max_length=100)
    parameter=models.CharField(max_length=100)
    description=models.CharField(max_length=100)
    def __str__(self):
        return self.tipo
class sensor_command(models.Model):
    actuacion=models.ForeignKey(sensor_actuacion,on_delete=models.CASCADE)
    device_id=models.ForeignKey(mqtt_msg,on_delete=models.CASCADE,limit_choices_to={'feed__iexact':'shellies','device_id__icontains':'-'})
    circuit=models.IntegerField(default=0)

    def __str__(self):
        return self.actuacion.description

class router_parameter(models.Model):
    parameter=models.CharField(max_length=100)
    description=models.CharField(max_length=100)
    def __str__(self):
        return self.parameter
class router_get(models.Model):
    parameter=models.ForeignKey(router_parameter,on_delete=models.CASCADE)
    device_id=models.ForeignKey(mqtt_msg,on_delete=models.CASCADE,limit_choices_to={'feed__iexact':'router'})
    def __str__(self):
        return self.parameter.parameter+'_'+self.device_id.device_id

# @receiver(post_save, sender=sensor_command)
# def send_command(sender, instance,created, **kwargs):
#     if created:
#         device_id=instance.device_id.device_id
#         topic=instance.actuacion.command.replace('device_id',device_id)
#         print('sending command',topic,instance.actuacion.parameter)
#         mqtt.client.publish(topic,instance.actuacion.parameter)
#         instance.delete()
#
# @receiver(post_save, sender=router_get)
# def get_router_parameter(sender, instance,created, **kwargs):
#     if created:
#         device_id=instance.device_id.device_id
#         topic='get/serial/command'.replace('serial',device_id)
#         print('sending command',topic,instance.parameter.parameter)
#         mqtt.client.publish(topic,instance.parameter.parameter)
#         instance.delete()