from hashlib import md5
from urllib.parse import urlencode

from django import template
from django.conf import settings
from sorl.thumbnail import get_thumbnail

register = template.Library()

AVATAR_DEFAULT = getattr(settings, "USER_AVATAR_DEFAULT", "retro")
AVATAR_SSL = getattr(settings, "USER_AVATAR_SSL", True)

GRAVATAR_SECURE_BASE_URL = "https://secure.gravatar.com/avatar/"
GRAVATAR_BASE_URL = "http://www.gravatar.com/avatar/"


def _gravatar_url(email, size, default, secure):
    email_hash = md5(email.strip().lower().encode()).hexdigest()
    base_url = GRAVATAR_SECURE_BASE_URL if secure else GRAVATAR_BASE_URL
    query = urlencode({"s": size, "r": "g", "d": default})
    return f"{base_url}{email_hash}?{query}"


@register.simple_tag
def get_avatar_url(user, width=80, height=80, default=None):
    if user.picture:
        geometry_string = "{width}x{height}".format(width=width, height=height)
        return get_thumbnail(file_=user.picture, geometry_string=geometry_string).url
    return _gravatar_url(
        email=user.email,
        size=width,
        default=default or AVATAR_DEFAULT,
        secure=AVATAR_SSL,
    )
