from os.path import splitext

from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()


@register.filter
def letter2panel(obj):
    if obj.genre == obj.GENRE.comment:
        return "panel-info"
    return "panel-primary" if obj.created_by_is_staff else "panel-default"


@register.filter
@stringfilter
def file2css(path):
    """Converts a file into class name"""
    _, ext = splitext(path)
    return {
        ".pdf": "far fa-file-pdf",
        ".zip": "far fa-file-zipper",
        ".rar": "far fa-file-zipper",
        ".7z": "far fa-file-zipper",
        ".tar": "far fa-file-zipper",
        ".gz": "far fa-file-zipper",
        ".xlsx": "far fa-file-excel",
        ".xlsm": "far fa-file-excel",
        ".xlsb": "far fa-file-excel",
        ".xltx": "far fa-file-excel",
        ".xltm": "far fa-file-excel",
        ".xls": "far fa-file-excel",
        ".xlt": "far fa-file-excel",
        ".xlam": "far fa-file-excel",
        ".xlw": "far fa-file-excel",
        ".csv": "far fa-file-excel",
        ".dbf": "far fa-file-excel",
        ".jpg": "far fa-file-image",
        ".png": "far fa-file-image",
        ".tiff": "far fa-file-image",
        ".gif": "far fa-file-image",
        ".svg": "far fa-file-image",
        ".cpp": "far fa-file-code",
        ".js": "far fa-file-code",
        ".py": "far fa-file-code",
        ".html": "far fa-file-code",
        ".html": "far fa-file-code",
        ".rtf": "far fa-file-word",
        ".doc": "far fa-file-word",
        ".dot": "far fa-file-word",
        ".docx": "far fa-file-word",
        ".docm": "far fa-file-word",
        ".dotx": "far fa-file-word",
        ".dotm": "far fa-file-word",
        ".docb": "far fa-file-word",
        ".docb": "far fa-file-word",
        ".odt": "far fa-file-word",
        ".ott": "far fa-file-word",
        ".oth": "far fa-file-word",
        ".odm": "far fa-file-word",
        ".odp": "far fa-file-powerpoint",
        ".otp": "far fa-file-powerpoint",
        ".odg": "far fa-file-powerpoint",
        ".ppt": "far fa-file-powerpoint",
        ".pot": "far fa-file-powerpoint",
        ".mp3": "far fa-file-audio",
        ".ogg": "far fa-file-audio",
        ".oga": "far fa-file-audio",
        ".wma": "far fa-file-audio",
        ".wav": "far fa-file-audio",
        ".m4a": "far fa-file-audio",
        ".flac": "far fa-file-audio",
        ".acc": "far fa-file-audio",
        ".txt": "far fa-file-lines",
        ".avi": "far fa-file-video",
        ".mp4": "far fa-file-video",
        ".webm": "far fa-file-video",
    }.get(ext, "far fa-file")
