from django.db import models
from django.db.models.query import QuerySet
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from poradnia.users.models import User

from .utils import make_random_password

try:
    from django.core.urlresolvers import reverse
except ImportError:
    from django.urls import reverse


class KeyQuerySet(QuerySet):
    def for_user(self, user):
        return self.filter(user=user)


@python_2_unicode_compatible
class Key(models.Model):
    user = models.ForeignKey(User, verbose_name=_("User"), on_delete=models.CASCADE)
    password = models.CharField(max_length=75, default=make_random_password, verbose_name=_("Key"))
    description = models.CharField(max_length=75, verbose_name=_("Description"))
    created_on = models.DateTimeField(auto_now_add=True, verbose_name=_("Created on"))
    used_on = models.DateTimeField(null=True, verbose_name=_("Used on"))
    download_on = models.DateTimeField(null=True, verbose_name=_("Download on"))
    objects = KeyQuerySet.as_manager()

    def get_absolute_url(self):
        return reverse('keys:details', kwargs={'pk': self.pk})

    def __str__(self):
        return "%s" % (self.created_on)

    class Meta:
        unique_together = (("user", "password"),)
        verbose_name = _("Access key")
        verbose_name_plural = _("Access keys")
