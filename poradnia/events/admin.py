from django.contrib import admin

from .models import Event, Reminder


class ReminderInline(admin.StackedInline):
    model = Reminder


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    inlines = [ReminderInline]
