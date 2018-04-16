from django.core.checks import Error, register
from django.utils.module_loading import import_string

from poradnia.stats.settings import STAT_METRICS


@register()
def stat_metrics_check(app_configs, **kwargs):
    errors = []
    for key, value in STAT_METRICS.items():
        try:
            import_string(value)
        except ImportError:
            errors.append(
                Error(
                    'I can not load {} as a statistical metric.'.format(value),
                    hint='Update STAT_METRICS[\"{}\"] settings .'.format(key),
                    obj=key,
                    id='stats.E001',
                )
            )
    return errors
