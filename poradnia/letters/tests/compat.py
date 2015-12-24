import django


def refresh_from_db(obj):
    if django.VERSION >= (1, 8):
        obj.refresh_from_db()
        return obj
    else:
        return obj._meta.model.objects.get(pk=obj.pk)
