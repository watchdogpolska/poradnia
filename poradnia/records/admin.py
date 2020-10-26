from django.contrib import admin

from .models import Record

admin.site.register(Record)


class RecordInline(admin.StackedInline):
    """
    Stacked Inline View for Record
    """

    model = Record
