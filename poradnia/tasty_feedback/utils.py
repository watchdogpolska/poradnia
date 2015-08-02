from django.utils.module_loading import import_string
from django.conf import settings


def get_form(genre='submit'):
    return import_string(getattr(settings, 'FEEDBACK_FORM_SUBMIT',
        'tasty_feedback.forms.FeedbackForm'))


def get_filter():
    return import_string(getattr(settings, 'FEEDBACK_FILTER',
        'tasty_feedback.filters.FeedbackFilter'))


def githubify(text):
    return u">"+text.replace("\n", "\n>")+"\n\nby django-tasty-feedback"
