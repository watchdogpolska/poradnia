from django.contrib import admin
from guardian.admin import GuardedModelAdmin
from .models import Case


@admin.register(Case)
class CaseAdmin(GuardedModelAdmin):
    list_display = ['name', 'client']
