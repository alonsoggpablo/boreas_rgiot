from django import template
import json

register = template.Library()

@register.filter
def get_field(obj, field_name):
    """Get field value from object, handling special types like JSON"""
    value = getattr(obj, field_name, '')
    
    # Format JSON objects nicely
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, indent=2)
    
    return value if value is not None else ''
