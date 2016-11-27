# -*- coding: utf-8 -*-
from braces.views import LoginRequiredMixin, StaffuserRequiredMixin
from django.core.urlresolvers import reverse
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.forms import modelform_factory
from django.utils.translation import ugettext_lazy as _
from django.views.generic import DetailView, RedirectView, UpdateView
from django_filters.views import FilterView

from .filters import UserFilter
from .forms import ProfileForm, UserForm
from .models import Profile, User
from .utils import PermissionMixin


class UserDetailView(PermissionRequiredMixin, DetailView):
    model = User
    slug_field = "username"
    slug_url_kwarg = "username"
    permission_required = "users.can_view_other"
    raise_exception = True

    def has_permission(self, *args, **kwargs):
        if self.kwargs['username'] == self.request.user.username:
            return True
        return super(UserDetailView, self).has_permission(*args, **kwargs)


class UserRedirectView(LoginRequiredMixin, RedirectView):
    permanent = False

    def get_redirect_url(self):
        return reverse("users:detail",
                       kwargs={"username": self.request.user.username})


class UserUpdateView(LoginRequiredMixin, UpdateView):

    form_class = UserForm

    # we already imported User in the view code above, remember?
    model = User

    # send the user back to their own page after a successful update
    def get_success_url(self):
        return reverse("users:detail",
                       kwargs={"username": self.request.user.username})

    def get_object(self):
        # Only get the User record for the user making the request
        return User.objects.get(username=self.request.user.username)


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    form_class = ProfileForm
    model = Profile

    def get_success_url(self):
        return reverse("users:detail",
                       kwargs={"username": self.request.user.username})

    def get_object(self):
        # Only get the User record for the user making the request
        return Profile.objects.get_or_create(user=self.request.user)[0]

    def get_form(self, *args, **kwargs):
        # dynamically exclude event_reminder_time if user is not a staff member
        if not self.request.user.is_staff:
            exclude = ('event_reminder_time',)

            self.form_class = modelform_factory(model=self.model,
                                                form=self.form_class,
                                                exclude=exclude)

        return super(ProfileUpdateView, self).get_form(*args, **kwargs)


class UserListView(StaffuserRequiredMixin, PermissionMixin, FilterView):
    model = User
    slug_field = "username"
    slug_url_kwarg = "username"
    filterset_class = UserFilter
    paginate_by = 25
    IS_STAFF_FILTER = ((_("All users"), {}),
                       (_("Staff"), {'is_staff': True}),
                       ((_("Clients"), {'is_staff': False})),
                       )

    def get_is_staff_choice(self):
        if 'is_staff' not in self.request.GET:
            return 0
        if not self.request.GET['is_staff'].isdigit():
            return 0
        num = int(self.request.GET['is_staff'])
        if len(self.IS_STAFF_FILTER) < num:
            return 0
        return num

    def get_queryset(self, *args, **kwargs):
        qs = super(UserListView, self).get_queryset(*args, **kwargs)
        qs = qs.filter(**self.IS_STAFF_FILTER[self.get_is_staff_choice()][1])
        qs = qs.with_case_count()
        if self.request.user.has_perm('cases.can_assign'):
            qs = qs.with_case_count_assigned()
        return qs

    def get_context_data(self, **kwargs):
        context = super(UserListView, self).get_context_data(**kwargs)
        context['is_staff'] = dict(choices=enumerate(self.IS_STAFF_FILTER),
                                   selected=self.get_is_staff_choice())
        return context
