# -*- coding: utf-8 -*-
# Import the reverse lookup function
# Only authenticated users can access views using this.
from braces.views import LoginRequiredMixin, StaffuserRequiredMixin
from django.core.urlresolvers import reverse
# view imports
from django.views.generic import DetailView, ListView, RedirectView, UpdateView

# Import the form from users/forms.py
from .forms import ProfileForm, UserForm
# Import the customized User model
from .models import Profile, User
from .utils import PermissionMixin


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


class UserListView(StaffuserRequiredMixin, PermissionMixin, ListView):
    model = User
    slug_field = "username"
    slug_url_kwarg = "username"

    def get_queryset(self, *args, **kwargs):
        qs = super(UserListView, self).get_queryset(*args, **kwargs)
        return qs.with_case_count()
