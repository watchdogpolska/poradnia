from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from poradnia.ai_assistant.tasks import (
    enqueue_case_delete_on_commit,
    enqueue_case_sync_on_commit,
)
from poradnia.template_mail.utils import TemplateKey, TemplateMailManager

from .models import Case, delete_files_for_cases


@receiver(post_save, sender=Case, dispatch_uid="new_case_notify")
def notify_new_case(sender, instance, created, **kwargs):
    if created:
        User = get_user_model()
        users = User.objects.filter(notify_new_case=True).all()
        email = [x.email for x in users]
        TemplateMailManager.send(
            template_key=TemplateKey.CASE_NEW,
            recipient_list=email,
            context={"case": instance},
        )


@receiver(post_save, sender=Case, dispatch_uid="assign_perm_new_case")
def assign_perm_new_case(sender, instance, created, **kwargs):
    if created:
        instance.assign_perm()


@receiver(pre_delete, sender=Case, dispatch_uid="delete_files_for_case")
def delete_files(sender, instance, **kwargs):
    delete_files_for_cases([instance])


@receiver(post_save, sender=Case, dispatch_uid="similar_cases_sync_on_status_change")
def sync_similar_cases_on_status_change(sender, instance, created, **kwargs):
    if not settings.SIMILAR_CASES_INDEX_ENABLED:
        return
    if not created and instance.tracker.has_changed("status"):
        enqueue_case_sync_on_commit(instance.pk)


# No sender filter: the 6-year cleanup deletes through the DeleteCaseProxy
# admin, and Django sends delete signals with the proxy class as sender.
@receiver(pre_delete, dispatch_uid="similar_cases_delete_on_case_delete")
def delete_from_similar_cases_index(sender, instance, **kwargs):
    if not settings.SIMILAR_CASES_INDEX_ENABLED:
        return
    if isinstance(instance, Case):
        enqueue_case_delete_on_commit(instance.pk)
