from django import template
from django.conf import settings
from gravatar import Gravatar
from sorl.thumbnail import get_thumbnail

register = template.Library()

AVATAR_DEFAULT = getattr(settings, "USER_AVATAR_DEFAULT", "retro")
AVATAR_SSL = getattr(settings, "USER_AVATAR_SSL", True)


@register.simple_tag
def get_avatar_url(user, width=80, height=80, default=None):
    if user.picture:
        geometry_string = "{width}x{height}".format(width=width, height=height)
        return get_thumbnail(file_=user.picture, geometry_string=geometry_string).url
    return Gravatar(
        email=user.email,
        secure=AVATAR_SSL,
        size=width,
        default=default or AVATAR_DEFAULT,
    ).thumb
