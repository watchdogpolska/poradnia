from __future__ import unicode_literals

from django.db import models
from django.db.models import QuerySet, Max
from django.utils.encoding import python_2_unicode_compatible
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _
from model_utils.models import TimeStampedModel

try:
    from django.core.urlresolvers import reverse
except ImportError:
    from django.urls import reverse


class ItemQueryset(QuerySet):
    def for_user(self, user):
        return self if user.is_staff else self.filter(public=True)

    def with_last_value(self):
        items = Value.objects.get_last_value(self)
        # result = []
        for item in Value.objects.all():
            item.last_value = items.get(item.pk, None)
        # result.append(item)
        yield item
        # return result


@python_2_unicode_compatible
class Item(TimeStampedModel):
    key = models.CharField(db_index=True, max_length=50, verbose_name=_("Metric key"))
    name = models.CharField(max_length=100, verbose_name=_("Name"))
    description = models.TextField(verbose_name=_("Description"), blank=True)
    last_updated = models.DateTimeField(null=True, blank=True,
                                        verbose_name=_("Time to get the last value"))
    public = models.BooleanField(default=True, verbose_name=_("Public?"),
                                 help_text="Select to publish metric for everyone on-line.")
    objects = ItemQueryset.as_manager()

    class Meta:
        verbose_name = _("Item")
        verbose_name_plural = _("Items")
        ordering = ['key', ]

    def __str__(self):
        if self.name == self.key:
            return self.name
        return "%s [%s]" % (self.name, self.key)

    def as_dict(self):
        return {'key': self.key,
                'name': self.name,
                'description': self.description,
                'last_updated': self.last_updated.strftime("%s"),
                'public': self.public}

    def get_absolute_url(self):
        return reverse('stats:item_detail', kwargs={'key': self.key})


class ValueQueryset(QuerySet):
    def get_last_value(self, items):
        return dict(self.filter(item_id__in=items).values_list('item_id').
                    annotate(Max('time')).values_list('item__id', 'value'))


class Value(models.Model):
    item = models.ForeignKey(Item)
    time = models.DateTimeField(db_index=True, default=now)
    value = models.IntegerField()
    comment = models.CharField(max_length=150)
    objects = ValueQueryset.as_manager()

    def as_dict(self):
        return {'time': self.time.strftime("%s"),
                'value': self.value,
                'comment': self.comment}

    class Meta:
        verbose_name = _("Value")
        verbose_name_plural = _("Values")
        ordering = ['item_id', 'time']


@python_2_unicode_compatible
class Graph(models.Model):
    name = models.CharField(verbose_name=_("Name"), max_length=100)
    description = models.TextField(verbose_name=_("Description"))
    items = models.ManyToManyField(Item, verbose_name=_("Items"))

    def get_absolute_url(self):
        return reverse('stats:graph_detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Graph")
        verbose_name_plural = _("Graphs")
