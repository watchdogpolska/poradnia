# -*- coding: utf-8 -*-
# Import the reverse lookup function
from django.core.urlresolvers import reverse
# view imports
from django.views.generic import DetailView
from django.views.generic import RedirectView
from django.views.generic import UpdateView
from django.views.generic import ListView

# Only authenticated users can access views using this.
from braces.views import LoginRequiredMixin

# Import the form from users/forms.py
from .forms import UserForm

# Import the customized User model
from .models import User

from cases.models import Case


class UserOrStaffOnlyMixin(object):
    def get_queryset(self, *args, **kwargs):
        queryset = super(UserOrStaffOnlyMixin, self).get_queryset(*args, **kwargs)
        return queryset.for_user(self.request.user)


class UserDetailView(LoginRequiredMixin, UserOrStaffOnlyMixin, DetailView):
    model = User
    # These next two lines tell the view to index lookups by username
    slug_field = "username"
    slug_url_kwarg = "username"

    def get_context_data(self, **kwargs):
        """
        Insert the single object into the context dict.
        """
        context = {}
        context['case_list'] = Case.objects.for_user(self.request.user).\
            filter(client=self.object).all()
        context.update(kwargs)
        return super(UserDetailView, self).get_context_data(**context)


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


class UserListView(LoginRequiredMixin, UserOrStaffOnlyMixin, ListView):
    model = User
    # These next two lines tell the view to index lookups by username
    slug_field = "username"
    slug_url_kwarg = "username"

    def get_queryset(self):
        queryset = super(UserListView, self).get_queryset()
        if self.request.user.has_perm('cases.can_view_all'):
            return queryset.with_case_count()
        return queryset
