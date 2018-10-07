from django.conf import settings

LETTER_RECEIVE_SECRET = getattr(settings, 'LETTER_RECEIVE_SECRET')
