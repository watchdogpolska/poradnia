"""
Celery configuration for the Poradnia project.

This configuration sets up Celery with RabbitMQ as the message broker
and Django's database for result storage.
"""

import os

from celery import Celery

# Set the default Django settings module for the 'celery' program
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")

app = Celery("poradnia")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()


# Example test task to verify Celery is working correctly and test
# results backend connectivity.
@app.task
def test_task(message="Hello from Celery!"):
    """Simple test task for infrastructure verification."""
    print(f"Test task executed: {message}")
    return f"Task completed: {message}"
