from django.contrib import admin

from .models import Advice, Area, InstitutionKind, Issue, PersonKind


@admin.register(Advice)
class RegisterAdmin(admin.ModelAdmin):
    readonly_fields = ('created_on', 'created_by', 'modified_by', 'modified_on')
    list_display = ['created_on', 'advicer', '__unicode__', 'person_kind', 'institution_kind',
                    'visible']
    list_display_links = ['__unicode__']
    list_filter = ['created_on', 'grant_on', 'advicer', 'visible']

    def get_queryset(self, request):
        qs = super(RegisterAdmin, self).get_queryset(request)
        return qs.for_user(request.user)


@admin.register(Issue, InstitutionKind, PersonKind, Area)
class CategoryAdmin(admin.ModelAdmin):
    pass
