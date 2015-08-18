from django.utils.module_loading import import_string
from django.conf import settings
from django.core.mail.message import EmailMultiAlternatives


def get_form(genre='submit'):
    return import_string(getattr(settings, 'FEEDBACK_FORM_SUBMIT',
        'tasty_feedback.forms.FeedbackForm'))


def get_filter():
    return import_string(getattr(settings, 'FEEDBACK_FILTER',
        'tasty_feedback.filters.FeedbackFilter'))


def githubify(text):
    return u">"+text.replace("\n", "\n>")+"\n\nby django-tasty-feedback"


def mail_managers_replyable(subject, message, fail_silently=False, connection=None,
                  html_message=None, reply_email=None):
    """Sends a message to the managers, as defined by the MANAGERS setting."""
    if not settings.MANAGERS:
        return
    if reply_email:
        headers = {'Reply-To': reply_email}
    else:
        headers = {}
    mail = EmailMultiAlternatives('%s%s' % (settings.EMAIL_SUBJECT_PREFIX, subject),
                message,  settings.SERVER_EMAIL, [a[1] for a in settings.MANAGERS],
                connection=connection, headers=headers)
    if html_message:
        mail.attach_alternative(html_message, 'text/html')
    mail.send(fail_silently=fail_silently)
