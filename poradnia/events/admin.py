from django.contrib import admin

from .models import Reminder, Event


class ReminderInline(admin.StackedInline):
    model = Reminder


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    inlines = [ReminderInline]
