from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.crypto import constant_time_compare
from django.utils.encoding import force_str
from django.utils.http import base36_to_int, urlsafe_base64_decode


class AccountActivationTokenGenerator(PasswordResetTokenGenerator):
    """Distinct salt so activation links can't be replayed as password-reset
    tokens (or vice versa); invalidates itself once a real password is set,
    since the hash covers `user.password`.

    Uses its own timeout instead of the global PASSWORD_RESET_TIMEOUT
    (Django default: 3 days): a case can stay open for weeks, and every
    letter sent to a not-yet-activated client carries a freshly-minted
    activation link (see letters/email/_activation_link.html), so a short
    timeout meant most of those links were already dead by the time a
    client got around to reading their inbox. check_token() is Django's
    implementation with the settings.PASSWORD_RESET_TIMEOUT lookup swapped
    for `timeout` below - there's no cleaner override point upstream.
    """

    key_salt = "poradnia.users.tokens.AccountActivationTokenGenerator"
    timeout = 60 * 60 * 24 * 30  # 30 days

    def check_token(self, user, token):
        if not (user and token):
            return False
        try:
            ts_b36, _hash = token.split("-")
        except ValueError:
            return False
        try:
            ts = base36_to_int(ts_b36)
        except ValueError:
            return False

        for secret in [self.secret, *self.secret_fallbacks]:
            if constant_time_compare(
                self._make_token_with_timestamp(user, ts, secret), token
            ):
                break
        else:
            return False

        if (self._num_seconds(self._now()) - ts) > self.timeout:
            return False
        return True


account_activation_token = AccountActivationTokenGenerator()


def get_user_from_uidb64(uidb64):
    """Shared by AccountActivationView and AccountActivationResendView -
    decodes the uid embedded in an activation URL back into a user, without
    regard to whether any token/password state is still valid."""
    User = get_user_model()
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        return User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return None
