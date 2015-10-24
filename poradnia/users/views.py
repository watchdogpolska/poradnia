# -*- coding: utf-8 -*-
from braces.views import LoginRequiredMixin, StaffuserRequiredMixin
from django.core.urlresolvers import reverse
from django.views.generic import DetailView, RedirectView, UpdateView
from django_filters.views import FilterView
from .forms import ProfileForm, UserForm
from django.utils.translation import ugettext_lazy as _
from .models import Profile, User
from .utils import PermissionMixin
from .filters import UserFilter


class UserDetailView(PermissionMixin, DetailView):
    model = User
    # These next two lines tell the view to index lookups by username
    slug_field = "username"
    slug_url_kwarg = "username"


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
        return qs.with_case_count()

    def get_context_data(self, **kwargs):
        context = super(UserListView, self).get_context_data(**kwargs)
        context['is_staff'] = dict(choices=enumerate(self.IS_STAFF_FILTER),
                                   selected=self.get_is_staff_choice())
        return context
