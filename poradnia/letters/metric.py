from django.db.models import Count, Sum
from django.db.models.query_utils import Q
from django.utils.translation import ugettext_lazy as _

from poradnia.letters.models import Letter
from poradnia.stats.utils import filter_month


def letter_total(*args, **kwargs):
    return Letter.objects.count()


letter_total.name = _("Letter count")
letter_total.description = _("Total letter registered")


def letter_month(*args, **kwargs):
    return filter_month(Letter.objects, "created_on").count()


letter_month.name = _("Letter monthly")
letter_month.description = _("Total number of letter processed in month")


def letter_way(filter):
    def internal(*args, **kwargs):
        return filter_month(Letter.objects, "created_on").filter(filter).count()

    return internal


letter_staff_email = letter_way(~Q(eml="") & Q(created_by__is_staff=True))
letter_staff_email.name = _("Letter of staff by email")
letter_staff_email.description = _("Monthly number of staff letter send by e-mail")

letter_staff_www = letter_way(Q(eml="") & Q(created_by__is_staff=True))
letter_staff_www.name = _("Letter of staff by WWW")
letter_staff_www.description = _("Monthly number of staff letter send by www")

letter_user_email = letter_way(~Q(eml="") & Q(created_by__is_staff=False))
letter_user_email.name = _("Letter of staff by email")
letter_user_email.description = _("Monthly number of user letter send by e-mail")

letter_user_www = letter_way(Q(eml="") & Q(created_by__is_staff=False))
letter_user_www.name = _("Letter of user by WWW")
letter_user_www.description = _("Monthly number of user letter send by WWW")


def documents_written_for_clients(*args, **kwargs):
    qs = Letter.objects.filter(created_by__is_staff=True).filter(
        status=Letter.STATUS.done
    )
    qs = qs.annotate(attachment_count=Count("attachment"))
    qs = qs.aggregate(value=Sum("attachment_count"))
    return qs["value"] or 0


documents_written_for_clients.name = _("Documents written for clients")
documents_written_for_clients.description = _(
    "Number of attachments in staff " "messages send to clients."
)
