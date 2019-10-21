from django.utils.translation import ugettext_lazy as _

from poradnia.cases.models import Case
from poradnia.stats.utils import filter_month


def cases_count(*args, **kwargs):
    return Case.objects.count()


cases_count.name = _("Cases count")
cases_count.description = _("Total cases registered")


def cases_status(status):
    def cases_for_status(*args, **kwargs):
        return Case.objects.filter(status=status).count()

    return cases_for_status


cases_free = cases_status(Case.STATUS.free)
cases_free.name = _("Cases free")
cases_free.description = _("Count of cases status free")

cases_assigned = cases_status(Case.STATUS.assigned)
cases_assigned.name = _("Cases assigned")
cases_assigned.description = _("Count of cases status assigned")

cases_closed = cases_status(Case.STATUS.closed)
cases_closed.name = _("Cases closed")
cases_closed.description = _("Count of cases status closed")


def cases_monthly(*args, **kwargs):
    return filter_month(Case.objects, "created_on").count()


cases_monthly.name = _("Cases monthly")
cases_monthly.description = _("Number of cases registered in month")
