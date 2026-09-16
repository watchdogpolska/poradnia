from django.contrib.auth import get_user_model
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

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
