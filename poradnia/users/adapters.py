from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.core.exceptions import PermissionDenied


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        # Only enforce for providers that supply verification status.
        extra = sociallogin.account.extra_data or {}
        email = extra.get("email")
        email_verified = extra.get("email_verified")

        # If provider didn't assert verification, don't auto-link based on email.
        if email and email_verified is False:
            raise PermissionDenied("Email not verified by provider.")
