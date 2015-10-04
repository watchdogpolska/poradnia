import base64

from django.http import HttpResponse
from django.utils.timezone import now

from .models import Key


class KeyAuthMixin(object):
    def get_user_data(self, request):
        if 'HTTP_AUTHORIZATION' in request.META:
            auth = request.META['HTTP_AUTHORIZATION'].split()
            if len(auth) == 2 and auth[0].lower() == "basic":
                    return base64.b64decode(auth[1]).split(':')
        if 'user' in request.GET and 'password' in request.GET:
            return (request.GET['user'], request.GET['password'])
        return None

    def dispatch(self, request, *args, **kwargs):
        auth = self.get_user_data(request)
        if auth:
            uname, passwd = auth
            try:
                key = Key.objects.filter(user__username=uname, password=passwd).get()
                key.used_on = now()
                key.save()
                user = key.user
            except (Key.MultipleObjectsReturned, Key.DoesNotExist):
                user = None
            if user is not None and user.is_active:
                    request.user = user
                    return super(KeyAuthMixin, self).dispatch(request, *args, **kwargs)
        return HttpResponse('Unauthorized', status=401)
