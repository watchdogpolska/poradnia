from __future__ import unicode_literals

import logging
import os
from django.contrib.sites.shortcuts import get_current_site
from os.path import basename
from cached_property import cached_property
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files import File
from django.db import models
from django.db.models import F, Func, IntegerField, Q
from django.dispatch import receiver
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from django_mailbox.models import Message
from django_mailbox.signals import message_received
from model_utils import Choices
from model_utils.fields import MonitorField, StatusField
import talon

from poradnia.cases.models import Case
from poradnia.cases.utils import get_users_with_perm
from poradnia.records.models import AbstractRecord, AbstractRecordQuerySet
from poradnia.users.models import User

from .utils import date_random_path

try:
    from django.core.urlresolvers import reverse
except ImportError:
    from django.urls import reverse

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


@python_2_unicode_compatible
class Letter(AbstractRecord):
    STATUS = Choices(('staff', _('Staff')), ('done', _('Done')))
    GENRE = Choices('mail', 'comment')
    genre = models.CharField(choices=GENRE, default=GENRE.comment, max_length=20)
    status = StatusField(db_index=True)
    status_changed = MonitorField(monitor='status')
    accept = MonitorField(monitor='status', when=['done'], verbose_name=_("Accepted on"))
    name = models.CharField(max_length=250, verbose_name=_("Subject"))
    text = models.TextField(verbose_name=_("Text"))
    html = models.TextField(verbose_name=_("HTML"), blank=True, null=True)
    signature = models.TextField(verbose_name=_("Signature"), blank=True, null=True)
    created_by = models.ForeignKey(to=settings.AUTH_USER_MODEL,
                                   related_name='letter_created_by',
                                   verbose_name=_("Created by"))
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

    def __str__(self):
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
        return True if self.status == self.STATUS.done else False

    def get_edit_url(self):
        return reverse('letters:edit', kwargs={'pk': self.pk})

    def get_send_url(self):
        return reverse('letters:send', kwargs={'pk': self.pk})

    def set_new_case(self):
        self.case = Case.objects.create(subject=self.name,
                                        created_by=self.created_by,
                                        client=self.client)

    def send_notification(self, *args, **kwargs):
        staff_users = get_users_with_perm(self.case, 'can_send_to_client')
        management = User.objects.filter(notify_unassigned_letter=True).all()
        if self.status is Letter.STATUS.done:
            if len(list(staff_users)) > 0:
                kwargs['user_qs'] = self.get_users_with_perms()
            else:
                kwargs['user_qs'] = User.objects.filter(Q(pk__in=self.get_users_with_perms()) |
                                                        Q(pk__in=management))
        else:
            if len(list(staff_users)) > 0:
                kwargs['user_qs'] = self.get_users_with_perms().filter(is_staff=True)
            else:
                kwargs['user_qs'] = User.objects.filter(Q(pk__in=self.get_users_with_perms().filter(is_staff=True)) |
                                                        Q(pk__in=management))
        return super(Letter, self).send_notification(*args, **kwargs)

    class Meta:
        verbose_name = _('Letter')
        verbose_name_plural = _('Letters')
        ordering = ['-created_on']


@python_2_unicode_compatible
class Attachment(models.Model):
    letter = models.ForeignKey(Letter)
    attachment = models.FileField(upload_to=date_random_path, verbose_name=_("File"))

    @property
    def filename(self):
        return basename(self.attachment.name)

    def __str__(self):
        return "%s" % (self.filename)

    def get_absolute_url(self):
        return self.attachment.url

    def get_full_url(self):
        return ''.join(['https://', get_current_site(None).domain, self.get_absolute_url()])

    class Meta:
        verbose_name = _('Attachment')
        verbose_name_plural = _('Attachments')


class MessageParser(object):
    def __init__(self, message):
        self.message = message
        self.email_object = message.get_email_object()

    @staticmethod
    @receiver(message_received)
    def receive_signal(sender, message, **kwargs):
        MessageParser(message).insert()

    @cached_property
    def from_address(self):
        return self.message.from_address[0]

    def is_autoreply(self):
        return self.email_object.get('Auto-Submitted', None) == 'auto-replied'

    @cached_property
    def actor(self):
        return get_user_model().objects.get_by_email_or_create(self.from_address)

    @cached_property
    def case(self):
        try:
            case = Case.objects.by_msg(self.message).get()
        except Case.DoesNotExist:
            case = Case.objects.create(name=self.message.subject,
                                       created_by=self.actor,
                                       client=self.actor)
            self.actor.notify(actor=self.actor, verb='registered', target=case, from_email=case.get_email())
        return case

    @cached_property
    def quote(self):
        if self.message.text:
            return self.message.text.replace(self.text, '')
        return self.message.text.replace(self.text, '')

    @cached_property
    def text(self):
        if self.message.text:
            return talon.quotations.extract_from(self.message.text)
        return talon.quotations.extract_from(self.message.html, 'text/html')

    @cached_property
    def html(self):
        if self.message.html:
            return talon.quotations.extract_from_html(self.message.html)
        else:
            return None

    @cached_property
    def letter_status(self):
        if self.actor.is_staff and not self.actor.has_perm('cases.can_send_to_client', self.case):
            return Letter.STATUS.staff
        else:
            return Letter.STATUS.done

    def save_letter(self):
        return Letter.objects.create(name=self.message.subject,
                                     created_by=self.actor,
                                     case=self.case,
                                     status=self.letter_status,
                                     text=self.text,
                                     html=self.html,
                                     message=self.message,
                                     signature=self.quote,
                                     eml=self.message.eml)

    def save_attachments(self, letter):
        attachments = []
        for attachment in self.message.attachments.all():
            name = attachment.get_filename() or 'Unknown.bin'
            if len(name) > 70:
                name, ext = os.path.splitext(name)
                ext = ext[:70]
                name = name[:70 - len(ext)] + ext
            att_file = File(attachment.document, name)
            att = Attachment(letter=letter, attachment=att_file)
            attachments.append(att)
        Attachment.objects.bulk_create(attachments)
        return attachments

    def insert(self):
        # Skip autoreply messages - see RFC3834
        if self.is_autoreply():
            logger.info("Delete .eml from {email} as auto-replied".format(email=self.from_address))
            self.message.eml.delete(save=True)
            return

        letter = self.save_letter()
        logger.info("Message #{message} registered in case #{case} as letter #{letter}".
                    format(message=self.message.pk,
                           case=self.case.pk,
                           letter=letter.pk))
        attachments = self.save_attachments(letter)
        logger.debug("Saved {attachment_count} attachments for letter #{letter}".
                     format(attachment_count=len(attachments),
                            letter=letter.pk))
        self.case_update(self.case)
        letter.send_notification(actor=self.actor, verb='created')

    def case_update(self, case):
        if case.status == Case.STATUS.closed and self.letter_status == Letter.STATUS.done:  # re-open
            case.status_update(reopen=True, save=False)

        if case.handled is False and self.actor.is_staff is True and self.letter_status == Letter.STATUS.done:
            case.handled = True
        elif case.handled is False and self.actor.is_staff is False:
            case.handled = False
        self.case.update_counters()
        case.save()
