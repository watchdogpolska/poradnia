from django.db import models
from django.core.urlresolvers import reverse


class Style(models.Model):
    name = models.CharField(max_length=30)
    code = models.CharField(max_length=30, unique=True)

    def __unicode__(self):
        return self.name


class Tag(models.Model):
    style = models.ForeignKey(Style)
    name = models.CharField(max_length=10)

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('cases:list')+'?tag='+str(self.pk)
