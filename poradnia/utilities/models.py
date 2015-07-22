from os.path import basename
from django.db import models
from django.utils.translation import ugettext_lazy as _


class AttachmentBase(models.Model):
    attachment = models.FileField(upload_to="letters/%Y/%m/%d", verbose_name=_("File"))

    @property
    def filename(self):
        return basename(self.attachment.name)

    def __unicode__(self):
        return "%s" % (self.filename)

    def get_absolute_url(self):
        return self.attachment.url

    class Meta:
        abstract = True
        verbose_name = _('Attachment')
        verbose_name_plural = _('Attachments')
