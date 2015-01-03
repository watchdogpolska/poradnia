from django.contrib import admin
from .models import Tag, Style
# Register your models here.

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    pass

@admin.register(Style)
class StyleAdmin(admin.ModelAdmin):
    pass
