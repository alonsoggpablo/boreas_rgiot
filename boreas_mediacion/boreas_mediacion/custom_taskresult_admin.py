from django.contrib import admin
from django_celery_results.models import TaskResult
import json

class CustomTaskResultAdmin(admin.ModelAdmin):
    list_display = (
        'task_id', 'status', 'date_done', 'task_name', 'periodic_task_name', 'result_short',
    )
    search_fields = ('task_id', 'status', 'result')
    readonly_fields = [f.name for f in TaskResult._meta.fields]

    def periodic_task_name(self, obj):
        try:
            result = obj.result
            if result:
                data = json.loads(result)
                return data.get('periodic_task_name', '')
        except Exception:
            return ''
        return ''
    periodic_task_name.short_description = 'Periodic Task Name'

    def result_short(self, obj):
        result = obj.result
        if result and len(result) > 75:
            return result[:75] + '...'
        return result
    result_short.short_description = 'Result (truncated)'
