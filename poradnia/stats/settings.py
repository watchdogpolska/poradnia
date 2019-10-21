from django.conf import settings

STAT_METRICS = getattr(settings, "STAT_METRICS", {})
