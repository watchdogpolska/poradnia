from django.contrib import admin
from django.db.models import Count

from cases.tags.models import Style, Tag


# Register your models here.


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'style', 'get_case_count']
    list_filter = ['style', ]

    def get_case_count(self, obj):
        return obj.case_count

    def get_queryset(self, *args, **kwargs):
        qs = super(TagAdmin, self).get_queryset(*args, **kwargs)
        return qs.annotate(case_count=Count('case'))


@admin.register(Style)
class StyleAdmin(admin.ModelAdmin):
    pass
