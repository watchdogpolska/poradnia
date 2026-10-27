from __future__ import annotations

from .ui_mode import UI_MODE_NORMAL


def ui_mode(request):
    return {"ui_mode": getattr(request, "ui_mode", UI_MODE_NORMAL)}
