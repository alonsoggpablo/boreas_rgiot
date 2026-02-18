
from django.contrib import admin
from django_celery_results.models import TaskResult

class MinimalTaskResultAdmin(admin.ModelAdmin):
    list_display = ('result', 'date_done', 'status')
    search_fields = ('result',)
    readonly_fields = [f.name for f in TaskResult._meta.fields]
