from django.conf import settings
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from poradnia.ai_assistant.models import SimilarCasesIndexState
from poradnia.ai_assistant.tasks import (
    enqueue_case_sync_on_commit,
    enqueue_scope_sync_on_commit,
)
from poradnia.cases.models import Case

from .models import Advice, Scope

SIMILAR_CASES_SCOPE_FLAGS = (
    "is_dip",
    "is_local_government",
    "is_slapp",
    "is_out_of_scope",
)


def _may_be_in_similar_cases_index(case_id):
    return (
        Case.objects.filter(pk=case_id, status=Case.STATUS.closed).exists()
        or SimilarCasesIndexState.objects.filter(case_id=case_id).exists()
    )


@receiver(post_save, sender=Advice, dispatch_uid="similar_cases_sync_on_advice_save")
@receiver(
    post_delete, sender=Advice, dispatch_uid="similar_cases_sync_on_advice_delete"
)
def sync_similar_cases_on_advice_change(sender, instance, **kwargs):
    if not settings.SIMILAR_CASES_INDEX_ENABLED:
        return
    if instance.case_id and _may_be_in_similar_cases_index(instance.case_id):
        enqueue_case_sync_on_commit(instance.case_id)


@receiver(pre_save, sender=Scope, dispatch_uid="similar_cases_remember_scope_flags")
def remember_scope_flags(sender, instance, **kwargs):
    if not settings.SIMILAR_CASES_INDEX_ENABLED or not instance.pk:
        return
    instance._similar_cases_old_flags = (
        Scope.objects.filter(pk=instance.pk)
        .values_list(*SIMILAR_CASES_SCOPE_FLAGS)
        .first()
    )


@receiver(post_save, sender=Scope, dispatch_uid="similar_cases_sync_on_scope_flags")
def sync_similar_cases_on_scope_flags(sender, instance, created, **kwargs):
    if not settings.SIMILAR_CASES_INDEX_ENABLED or created:
        return
    old_flags = getattr(instance, "_similar_cases_old_flags", None)
    new_flags = tuple(getattr(instance, flag) for flag in SIMILAR_CASES_SCOPE_FLAGS)
    if old_flags is not None and old_flags != new_flags:
        enqueue_scope_sync_on_commit(instance.pk)
