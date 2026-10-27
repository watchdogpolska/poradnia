from __future__ import annotations

import contextvars

UI_MODE_COOKIE_NAME = "ui_mode"
UI_MODE_NORMAL = "normal"
UI_MODE_WCAG = "wcag"
UI_MODES = (UI_MODE_NORMAL, UI_MODE_WCAG)

# Set by UiModeMiddleware for every request; code paths that never receive a
# request (Celery tasks, management commands, email rendering) keep the
# default below, which is exactly the "normal" fallback the design calls for.
_ui_mode_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "ui_mode", default=UI_MODE_NORMAL
)


def resolve_ui_mode(raw_value: str | None) -> str:
    """Normalize a raw cookie/POST value to one of the two allowed modes."""
    return raw_value if raw_value in UI_MODES else UI_MODE_NORMAL


def get_ui_mode() -> str:
    """Current UI mode for code that has no ``request`` to read from."""
    return _ui_mode_var.get()
