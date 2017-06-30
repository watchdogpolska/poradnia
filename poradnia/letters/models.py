from __future__ import unicode_literals

import logging
import os
from os.path import basename

import talon
import html2text
from poradnia.cases.models import Case
from talon import quotations
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files import File
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import F, Func, IntegerField
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _
from django_mailbox.models import Message
from django_mailbox.signals import message_received
from model_utils import Choices
from model_utils.fields import MonitorField, StatusField
from poradnia.records.models import AbstractRecord, AbstractRecordQuerySet

from .utils import date_random_path

talon.init()

logger = logging.getLogger(__name__)


class LetterQuerySet(AbstractRecordQuerySet):
    def for_user(self, user):
        qs = super(LetterQuerySet, self).for_user(user)
        if not user.is_staff:
            qs = qs.filter(status=Letter.STATUS.done)
        return qs

    def last_staff_send(self):
        return self.filter(status='done', created_by__is_staff=True).order_by(
                '-created_on', '-id').all()[0]

    def last_received(self):
        return self.filter(created_by__is_staff=False).order_by('-created_on', '-id').all()[0]

    def last(self):
        return self.order_by('-created_on', '-id').all()[0]

    def case(self, case):
        return self.filter(record__case=case)

    def with_month_year(self):
        return self.annotate(
                month=Func(F('created_on'),
                           function='month',
                           output_field=IntegerField())
            ).annotate(
                year=Func(F('created_on'),
                          function='year',
                          output_field=IntegerField())
            )


class Letter(AbstractRecord):
    STATUS = Choices(('staff', _('Staff')), ('done', _('Done')))
    GENRE = Choices('mail', 'comment')
    genre = models.CharField(choices=GENRE, default=GENRE.comment, max_length=20)
    status = StatusField(db_index=True)
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
    eml = models.FileField(
        _(u'Raw message contents'),
        null=True,
        upload_to="messages",
        help_text=_(u'Original full content of message')
    )

    objects = LetterQuerySet.as_manager()

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

    def set_new_case(self):
        self.case = Case.objects.create(subject=self.name,
                                        created_by=self.created_by,
                                        client=self.client)

    def send_notification(self, staff=None, *args, **kwargs):
        if self.status is Letter.STATUS.done:
            kwargs['staff'] = None
        else:
            kwargs['staff'] = True
        return super(Letter, self).send_notification(*args, **kwargs)

    class Meta:
        verbose_name = _('Letter')
        verbose_name_plural = _('Letters')
        ordering = ['-created_on']


class Attachment(models.Model):
    letter = models.ForeignKey(Letter)
    attachment = models.FileField(upload_to=date_random_path, verbose_name=_("File"))

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
    # new_user + poradnia@ => new_user @ new_user
    # new_user + case => FAIL
    # old_user + case => PASS
    # many_case => FAIL

    # Skip autoreply messages - see RFC3834
    if (lambda x: 'Auto-Submitted' in x and
            x['Auto-Submitted'] == 'auto-replied')(message.get_email_object()):
        logger.info("Delete .eml from {email} as auto-replied".format(
                    email=message.from_address[0]))
        message.eml.delete(save=True)
        return

    # Identify user
    user = get_user_model().objects.get_by_email_or_create(message.from_address[0])
    logger.debug("Identified user: %s", user)

    # Identify case
    try:  # TODO: Is it old case?
        case = Case.objects.by_msg(message).get()
    except Case.DoesNotExist:
        logger.debug("Case creating")
        case = Case(name=message.subject, created_by=user, client=user)
        case.save()
        user.notify(actor=user, verb='registered', target=case, from_email=case.get_email())
    logger.debug("Case: %s", case)
    # Prepare text
    if message.text:
        text = quotations.extract_from(message.text, 'text/plain')
        signature = message.text.replace(text, '')
    else:
        text = html2text.html2text(quotations.extract_from(message.html, 'text/html'))
        signature = message.text.replace(text, '')

    # Calculate letter status
    if user.is_staff:
        if user.has_perm('cases.can_send_to_client', case):
            status = Letter.STATUS.done
        else:
            status = Letter.STATUS.staff
    else:
        status = Letter.STATUS.done

    # Update case status (re-open)
    case_updated = False
    if not user.is_staff and case.status == Case.STATUS.closed:
        case.status_update(reopen=True, save=False)
        case_updated = True
    if user.is_staff:
        case.handled = True
        case_updated = True
    if user.is_staff and status == Letter.STATUS.done:
        case.has_project = False
        case_updated = True

    if case_updated:
        case.save()

    obj = Letter(name=message.subject,
                 created_by=user,
                 case=case,
                 status=status,
                 text=text,
                 message=message,
                 signature=signature,
                 eml=message.eml)
    obj.save()

    logger.debug("Letter: %s", obj)
    # Convert attachments
    attachments = []
    for attachment in message.attachments.all():
        name = attachment.get_filename() or 'Unknown.bin'
        if len(name) > 70:
            name, ext = os.path.splitext(name)
            ext = ext[:70]
            name = name[:70 - len(ext)] + ext
        att_file = File(attachment.document, name)
        att = Attachment(letter=obj, attachment=att_file)
        attachments.append(att)
    Attachment.objects.bulk_create(attachments)
    case.update_counters()
    obj.send_notification(actor=user, verb='created')
