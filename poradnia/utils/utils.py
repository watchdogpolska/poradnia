def get_numeric_param(request, key):
    """Get numeric param from request"""
    value = None
    try:
        value = int(request.POST.get(key))
    except (TypeError, ValueError):
        pass
    return value
