import django


def refresh_from_db(obj):
    obj.refresh_from_db()
    return obj
