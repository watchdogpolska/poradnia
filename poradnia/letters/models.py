from os.path import basename
from django.db import models
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.core.files import File
from model_utils.fields import MonitorField, StatusField
from model_utils import Choices
from django.dispatch import receiver
from django_mailbox.signals import message_received
from django_mailbox.models import Message
from django.contrib.auth import get_user_model
import talon
from records.models import AbstractRecord
from template_mail.utils import send_tpl_email
from cases.models import Case

talon.init()


class Letter(AbstractRecord):
    STATUS = Choices(('staff', _('Staff')), ('done', _('Done')))
    GENRE = Choices('mail', 'comment')
    genre = models.CharField(choices=GENRE, default=GENRE.comment, max_length=20)
    status = StatusField()
    status_changed = MonitorField(monitor='status')
    accept = MonitorField(monitor='status', when=['done'], verbose_name=_("Accepted on"))
    name = models.CharField(max_length=250, verbose_name=_("Subject"))
    text = models.TextField(verbose_name=_("Text"))
    signature = models.TextField(verbose_name=_("Signature"), blank=True, null=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='letter_created_by', verbose_name=_("Created by"))
    created_on = models.DateTimeField(auto_now_add=True, verbose_name=_("Created on"))
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL,
                                    verbose_name=_("Modified by"),
                                    null=True,
                                    related_name='letter_modified_by')
    modified_on = models.DateTimeField(
        auto_now=True, null=True, blank=True, verbose_name=_("Modified on"))
    message = models.ForeignKey(Message, null=True, blank=True)

    def __unicode__(self):
        return self.name

    def get_users(self, force_all=False):
        users_to_notify = self.get_users_with_perms()

        if self.status == self.STATUS.staff or force_all:
            users_to_notify = users_to_notify.filter(is_staff=True)

        return users_to_notify

    def get_absolute_url(self):
        case_url = self.record.case_get_absolute_url()
        return "%s#letter-%s" % (case_url, self.pk)

    def is_done(self):
        return (True if self.status == self.STATUS.done else False)

    def get_edit_url(self):
        return reverse('letters:edit', kwargs={'pk': self.pk})

    def get_send_url(self):
        return reverse('letters:send', kwargs={'pk': self.pk})

    class Meta:
        verbose_name = _('Letter')
        verbose_name_plural = _('Letters')


class Attachment(models.Model):
    letter = models.ForeignKey(Letter)
    attachment = models.FileField(upload_to="letters/%Y/%m/%d", verbose_name=_("File"))

    @property
    def filename(self):
        return basename(self.attachment.name)

    def __unicode__(self):
        return "%s" % (self.filename)

    def get_absolute_url(self):
        return self.attachment.url

    class Meta:
        verbose_name = _('Attachment')
        verbose_name_plural = _('Attachments')


@receiver(message_received)
def mail_process(sender, message, **args):
    print "I just recieved a messtsage titled %s from a mailbox named %s" % (message.subject,
                                                                           message.mailbox.name, )
    # new_user + poradnia@ => new_user @ new_user
    # new_user + case => FAIL
    # old_user + case => PASS
    # many_case => FAIL

    # Identify user
    user = get_user_model().objects.get_by_email_or_create(message.from_address[0])
    print "Identified user: ", user

    # Skip autoreply messages - see RFC3834
    if (lambda x: 'Auto-Submitted' in 'x' and x['Auto-Submitted'] == 'auto-replied')(message.get_email_object()):
        print "Skip"
        return

    # Identify case
    try:  # TODO: Is it old case?
        case = Case.objects.by_msg(message).get()
    except Case.MultipleObjectsReturned:  # How many cases?
        print "Multiple case spam"
        send_tpl_email('case/email/case_many.txt', message.from_address[0],
            {'subject': message.subject})
        return
    except Case.DoesNotExist:
        print "Case creating"
        case = Case(name=message.subject, created_by=user, client=user)
        case.save()
        user.notify(actor=user, verb='registered', target=case, from_email=case.get_email())

    # Prepare text
    if message.text:
        text = talon.quotations.extract_from(message.text, 'text/plain')
        signature = message.text.replace(text, '')
    else:   # TODO: HTML strip (XSS injection)
        text = talon.quotations.extract_from(message.html, 'text/html')
        signature = message.text.replace(text, '')

    obj = Letter()
    obj.name = message.subject
    obj.created_by = user
    obj.case = case
    obj.status = Letter.STATUS.done
    obj.text = text
    obj.signature = signature
    obj.save()
    obj.send_notification(user, 'created')

    # Convert attachments
    attachments = []
    for attachment in message.attachments.all():
        attachments.add(Attachment(letter=obj, attachment=File(attachment.document, attachment.get_filename())))
    Attachment.objects.bulk_create(attachments)
    case.update_counters()

    print "Assing a message %s to case #%s as letter #%s" % (message.subject, case.pk, obj.pk)
