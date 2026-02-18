import json

def periodic_task_name(obj):
    try:
        result = obj.result
        if result:
            data = json.loads(result)
            return data.get('periodic_task_name', '')
    except Exception:
        return ''
    return ''

periodic_task_name.short_description = 'Periodic Task Name'

def result_short(obj):
    result = obj.result
    if result and len(result) > 75:
        return result[:75] + '...'
    return result

result_short.short_description = 'Result (truncated)'
