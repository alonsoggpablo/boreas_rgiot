# boreas_bot/models.py
# Dynamic models for all DEVICES* tables in the external database
from django.db import models
from django.conf import settings
from django.db import connections
from django.apps import apps

# Custom manager to always use the 'external' DB
from django.db import models

class ExternalDBManager(models.Manager):
	def get_queryset(self):
		return super().get_queryset().using('external')

# Models for external devices* tables

class DevicesROUTERS(models.Model):
	id = models.CharField(max_length=255, primary_key=True)
	name = models.CharField(max_length=255, blank=True, null=True)
	type = models.CharField(max_length=255, blank=True, null=True)
	mac = models.CharField(max_length=255, blank=True, null=True)

	objects = ExternalDBManager()

	class Meta:
		managed = False
		db_table = 'devicesROUTERS'


class DevicesNANOENVI(models.Model):
	uuid = models.CharField(max_length=255, primary_key=True)
	name = models.CharField(max_length=255, blank=True, null=True)
	client = models.CharField(max_length=255, blank=True, null=True)
	mac = models.CharField(max_length=32, blank=True, null=True)
	cp = models.CharField(max_length=255, blank=True, null=True)
	firmware = models.CharField(max_length=255, blank=True, null=True)
	broker = models.CharField(max_length=255, blank=True, null=True)
	site = models.CharField(max_length=255, blank=True, null=True)
	update = models.DateTimeField(blank=True, null=True)
	hw = models.CharField(max_length=255, blank=True, null=True)
	type_noise = models.BooleanField(blank=True, null=True)

	objects = ExternalDBManager()

	class Meta:
		managed = False
		db_table = 'devicesNANOENVI'


class DevicesCO2(models.Model):
	id = models.CharField(max_length=255, primary_key=True)
	client = models.CharField(max_length=255, blank=True, null=True)
	name = models.CharField(max_length=255, blank=True, null=True)
	update = models.DateTimeField(blank=True, null=True)
	mac = models.CharField(max_length=255, blank=True, null=True)
	nick = models.CharField(max_length=255, blank=True, null=True)
	ubicacion = models.CharField(max_length=255, blank=True, null=True)

	objects = ExternalDBManager()

	class Meta:
		managed = False
		db_table = 'devicesCO2'
