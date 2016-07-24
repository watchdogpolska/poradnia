# -*- coding: utf-8 -*-
from braces.views import LoginRequiredMixin, StaffuserRequiredMixin
from django.core.urlresolvers import reverse
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
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

    def handle_no_permission(self):
        if self.request.user.is_anonymous():
            return redirect('/konta/login/?next=%s' % self.request.path)
        else:
            return HttpResponseForbidden("403 - not authorized")

    def has_permission(self):
        user = self.request.user
        if user.has_perm("users.can_view_other") or self.request.path.startswith("/uzytkownik/{}/".format(user.username)):
            return True
        else:
            return False


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
