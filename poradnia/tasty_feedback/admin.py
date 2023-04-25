from django.contrib import admin

from poradnia.tasty_feedback.models import Feedback


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    date_hierarchy = "created"
    list_display = ["id", "user", "created", "url"]
    list_filter = ["status", "url"]
    search_fields = ["id", "url"]
    date_hierarchy = "created"
    actions = ["delete_selected"]
