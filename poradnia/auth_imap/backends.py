from imaplib import IMAP4, IMAP4_SSL

from django.contrib.auth import get_user_model


class IMAPAuthBackend(object):
    def authenticate(self, username=None, password=None, imap_cls=None):
        from auth_imap.settings import HOSTS

        part = username.split('@', 2)
        # Fast verify it is a e-mail
        if len(part) != 2:
            return None
        # Verify the domain
        if part[1] not in HOSTS:
            return None
        else:
            server = HOSTS[part[1]]

        if not imap_cls:  # TODO: How patch the better way?
            imap_cls = IMAP4_SSL if server.get('ssl', False) else IMAP4

        try:
            c = imap_cls(server['host'], server.get('port', 143))
            c.login(username, password)
            c.logout()
        except IMAP4.error:
            return None

        User = get_user_model()
        try:
            user = User.objects.get(email=username)
        except User.DoesNotExist:
            user = User.objects.create_user(username=username,
                                            email=username,
                                            password='')
            user.set_unusable_password()
            user.is_staff = server.get('staff', False)
            user.save()
        return user

    def get(self):
        from .settings import HOSTS
        return HOSTS
