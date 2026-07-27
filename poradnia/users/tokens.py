from django.contrib.auth.tokens import PasswordResetTokenGenerator


class AccountActivationTokenGenerator(PasswordResetTokenGenerator):
    """Distinct salt so activation links can't be replayed as password-reset
    tokens (or vice versa); invalidates itself once a real password is set,
    since the hash covers `user.password`."""

    key_salt = "poradnia.users.tokens.AccountActivationTokenGenerator"


account_activation_token = AccountActivationTokenGenerator()
