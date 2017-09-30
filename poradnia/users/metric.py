from django.utils.translation import ugettext_lazy as _
from django.utils.datetime_safe import datetime

from poradnia.users.models import User


def users_total(*args, **kwargs):
    return User.objects.count()


users_total.name = _("Users total")
users_total.description = _("Number of users registered total")


def users_monthly(*args, **kwargs):
    today = datetime.today().replace(day=1)
    return User.objects.filter(created_on__date__gte=today).count()


users_monthly.name = _("Users monthly")
users_monthly.description = _("Number of users registered in month")


def users_active(*args, **kwargs):
    return User.objects.active().count()


users_active.name = _("Active users")
users_active.description = _("Number of active users in month")


def users_active_staff(*args, **kwargs):
    return User.objects.active().filter(is_staff=True).count()


users_active_staff.name = _("Active staff member")
users_active_staff.description = _("Number of team members who have made at least one message in the current month.")
