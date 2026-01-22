# boreas_bot/admin.py
from django.contrib import admin
from django.apps import apps
from django.conf import settings
from django.db import connections
from django.utils.text import camel_case_to_spaces

# Register static models for devices* tables
from .models import DevicesROUTERS, DevicesNANOENVI, DevicesCO2


class ExternalDBAdmin(admin.ModelAdmin):

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.using('external')

    def get_search_results(self, request, queryset, search_term):
        queryset = queryset.using('external')
        return super().get_search_results(request, queryset, search_term)

    def get_list_filter(self, request):
        filters = super().get_list_filter(request)
        # If any filter uses a queryset, force it to use 'external'
        for f in filters:
            if hasattr(f, 'field') and hasattr(f.field, 'remote_field') and f.field.remote_field:
                rel_model = f.field.remote_field.model
                f.field.model = rel_model
        return filters

    def save_model(self, request, obj, form, change):
        obj.save(using='external')

    def delete_model(self, request, obj):
        obj.delete(using='external')

    def save_related(self, request, form, formsets, change):
        for formset in formsets:
            
            formset.save(using='external')

