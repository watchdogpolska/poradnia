from django.contrib import admin
from django.db.models import Count

from poradnia.stats.models import Graph, Item, Value


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    '''
        Admin View for Item
    '''
    list_display = ['name', 'key', 'description', 'last_updated', 'count_values', 'public']
    list_filter = ('name',)
    readonly_fields = ('key', 'last_updated')
    search_fields = ('key', 'name')

    def count_values(self, obj):
        return obj.count_values

    def get_queryset(self, request):
        qs = super(ItemAdmin, self).get_queryset(request)
        return qs.annotate(count_values=Count('value'))

    def get_list_display(self, request):
        def last_value(obj):
            if not getattr(self, '_cached_last_value', None):
                self._cached_last_value = Value.objects.get_last_value(self.get_queryset(request).values('id'))
            return self._cached_last_value.get(obj.pk, None)
        return super(ItemAdmin, self).get_list_display(request) + [last_value, ]


@admin.register(Graph)
class GraphAdmin(admin.ModelAdmin):
    '''
        Admin View for Item
    '''
    list_display = ['name', 'description', 'count_items']
    list_filter = ('items',)
    search_fields = ('name', 'description')

    def count_items(self, obj):
        return obj.count_items

    def get_queryset(self, request):
        qs = super(GraphAdmin, self).get_queryset(request)
        return qs.annotate(count_items=Count('items'))
