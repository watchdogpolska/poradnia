from django.contrib import admin
from mptt.admin import MPTTModelAdmin
from teryt_tree.models import JednostkaAdministracyjna


class JednostkaAdministracyjnaAdmin(MPTTModelAdmin):
    list_display = ["id", "name", "slug", "category", "parent", "updated_on", "active"]
    list_display_links = ["id", "name"]
    list_filter = ["category", "updated_on", "active"]
    search_fields = ["id", "name", "slug"]
    actions = None

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.unregister(JednostkaAdministracyjna)  # unregister original
admin.site.register(JednostkaAdministracyjna, JednostkaAdministracyjnaAdmin)
