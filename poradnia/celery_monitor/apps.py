from django.apps import AppConfig


class CeleryMonitorConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "poradnia.celery_monitor"
    verbose_name = "Celery / RabbitMQ Monitoring"
