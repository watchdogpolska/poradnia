from django.template import loader, Context
from django.core.mail import send_mail
from django.conf import settings


def send_tpl_email(template_name, recipient_list, context=None, from_email=None, **kwds):
    t = loader.get_template(template_name)
    c = Context(context or {})
    subject, txt = t.render(c).split("\n", 1)
    from_email = from_email if from_email else settings.DEFAULT_FROM_EMAIL
    send_mail(subject=subject.strip(),
              message=txt,
              from_email=from_email,
              recipient_list=recipient_list,
              **kwds)
