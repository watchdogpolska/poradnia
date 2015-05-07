from django.contrib import admin
from guardian.admin import GuardedModelAdmin
from .models import Case
from records.models import Record


class RecordInline(admin.StackedInline):
    '''
        Stacked Inline View for Record
    '''
    model = Record
    min_num = 3
    max_num = 20
    extra = 1


@admin.register(Case)
class CaseAdmin(GuardedModelAdmin):
    inlines = [RecordInline]
    list_display = ['name', 'client']
