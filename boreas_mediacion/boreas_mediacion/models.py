from django.db import models

class mqtt_msg(models.Model):
    report_time=models.DateTimeField(auto_now=True)
    device=models.JSONField(unique=True)
    device_id=models.CharField(max_length=100)
    measures=models.JSONField()

class reported_measure(models.Model):
    report_time=models.DateTimeField(auto_now=True)
    device=models.JSONField()
    measures=models.JSONField()