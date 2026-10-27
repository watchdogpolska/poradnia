from __future__ import annotations

from .ui_mode import UI_MODE_COOKIE_NAME, _ui_mode_var, resolve_ui_mode


class UiModeMiddleware:
    """Resolve the ``ui_mode`` cookie into ``request.ui_mode`` and into the
    ``ui_mode`` ContextVar (see ``poradnia.utils.ui_mode.get_ui_mode``), for
    the handful of code paths that render HTML without a request object.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        mode = resolve_ui_mode(request.COOKIES.get(UI_MODE_COOKIE_NAME))
        request.ui_mode = mode
        token = _ui_mode_var.set(mode)
        try:
            return self.get_response(request)
        finally:
            _ui_mode_var.reset(token)
