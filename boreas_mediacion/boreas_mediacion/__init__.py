


from .celery import app
# Ensure Celery registers all tasks in api_tasks.py
from . import api_tasks

__all__ = ("app",)





