# coding=utf-8
from datetime import timedelta

from django.utils.datetime_safe import datetime
import factory
import factory.fuzzy
import pytz


class ItemFactory(factory.django.DjangoModelFactory):
    key = factory.Sequence("item-key-{0}".format)
    name = factory.Sequence("item-name-{0}".format)
    description = factory.fuzzy.FuzzyText()
    last_updated = factory.Sequence(lambda n: datetime(2008, 1, 1, tzinfo=pytz.utc) + timedelta(days=n))
    public = True

    class Meta:
        model = 'stats.Item'


class ValueFactory(factory.django.DjangoModelFactory):
    item = factory.SubFactory("poradnia.stats.tests.factories.ItemFactory")
    time = factory.Sequence(lambda n: datetime(2008, 1, 1, tzinfo=pytz.utc) + timedelta(days=n))
    value = factory.Sequence(lambda n: n * n)
    comment = factory.Sequence("value-comment-{0}".format)

    class Meta:
        model = 'stats.Value'
