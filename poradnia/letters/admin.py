from django.contrib import admin, messages
from django.utils.translation import gettext_lazy as _

from .models import Attachment, Letter
from .tasks import update_attachment_text_content_task


class AttachmentInline(admin.StackedInline):
    """
    Stacked Inline View for Attachment
    """

    model = Attachment


@admin.register(Letter)
class LetterAdmin(admin.ModelAdmin):
    """
    Admin View for Letter
    """

    date_hierarchy = "created_on"
    list_display = (
        "pk",
        "genre",
        "status",
        "name",
        "get_case_name",
        "created_by",
        "created_by_is_staff",
        "created_on",
        "modified_by",
        "modified_on",
        "eml",
    )
    list_filter = (
        "genre",
        "status",
    )
    inlines = [AttachmentInline]
    search_fields = (
        "pk",
        "name",
        "record__case__name",
        "eml",
    )
    raw_id_fields = ()
    list_editable = ()
    ordering = ("-pk",)
    actions = ["enqueue_letter_attachments_text_extraction"]

    @admin.display(
        description=_("Case name"),
        ordering="record__case",
    )
    def get_case_name(self, obj):
        return obj.record.case.name

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        return qs.select_related("record__case")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    @admin.action(
        description=_(
            "Enqueue attacment text extraction tasks for selected letters (20s apart)"
        )
    )
    def enqueue_letter_attachments_text_extraction(self, request, queryset):
        attachment_ids = list(
            Attachment.objects.filter(letter__in=queryset)
            .order_by("-letter_id", "-pk")
            .values_list("pk", flat=True)
        )

        for index, attachment_pk in enumerate(attachment_ids):
            update_attachment_text_content_task.apply_async(
                args=[attachment_pk],
                countdown=index * 20,
            )

        self.message_user(
            request,
            _(
                f"Enqueued {len(attachment_ids)} attachment text extraction task(s) "
                f"from {queryset.count()} letter(s) with 20-second spacing."
            ),
            level=messages.SUCCESS,
        )


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    """
    Admin View for Attachment
    """

    list_display = (
        "pk",
        "letter",
        "attachment",
    )
    search_fields = (
        "pk",
        "letter__id",
        "attachment",
    )
    raw_id_fields = ("letter",)
    list_editable = ()
    ordering = ("-pk",)
    actions = ["enqueue_attachment_text_extraction"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    @admin.action(
        description=_("Enqueue text extraction for selected attachments (20s apart)")
    )
    def enqueue_attachment_text_extraction(self, request, queryset):
        attachment_ids = list(queryset.order_by("-pk").values_list("pk", flat=True))

        for index, attachment_pk in enumerate(attachment_ids):
            update_attachment_text_content_task.apply_async(
                args=[attachment_pk],
                countdown=index * 20,
            )

        self.message_user(
            request,
            _(
                f"Enqueued {len(attachment_ids)} attachment text extraction task(s) "
                f"with 20-second spacing."
            ),
            level=messages.SUCCESS,
        )
