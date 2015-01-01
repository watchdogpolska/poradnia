from django.contrib import admin
from .models import Case


class CaseAdmin(admin.ModelAdmin):
    list_display = ['name', 'client']

admin.site.register(Case, CaseAdmin)
