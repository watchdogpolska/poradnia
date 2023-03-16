from django.contrib import admin
from mptt.admin import MPTTModelAdmin

from teryt_tree.models import JednostkaAdministracyjna


class JednostkaAdministracyjnaAdmin(MPTTModelAdmin):
    list_display = ["id", "name", "slug", "category", "parent", "updated_on", "active"]
    list_display_links = ["id", "name"]
    list_filter = ["category", "updated_on", "active"]
    search_fields = ["id", "name", "slug"]
    actions = None


admin.site.unregister(JednostkaAdministracyjna)  # unregister original
admin.site.register(JednostkaAdministracyjna, JednostkaAdministracyjnaAdmin)
