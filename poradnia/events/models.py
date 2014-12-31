from django.db import models
from records.models import Record


class Event(Record):
    deadline = models.BooleanField(default=False)
    time = models.DateTimeField()
    text = models.CharField(max_length=150)


class Alarm(Record):
    event = models.ForeignKey(Event)