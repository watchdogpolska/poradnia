from django.contrib import admin

from .models import Alarm, Event

# Register your models here.

admin.site.register(Event)
admin.site.register(Alarm)
