import sys
from django.template import loader, Context
from django.core.mail import get_connection
from django.conf import settings
from django.core.mail.message import EmailMultiAlternatives


def send_mail_with_header(subject, message, from_email, recipient_list,
                          fail_silently=False, auth_user=None, auth_password=None,
                          connection=None, html_message=None, headers=None):
    """
    Fork of django.core.mail.send_mail to add haders attribute
    """
    connection = connection or get_connection(username=auth_user,
                                              password=auth_password,
                                              fail_silently=fail_silently)
    mail = EmailMultiAlternatives(subject, message, from_email, recipient_list,
                                  connection=connection, headers=headers or {})
    if html_message:
        mail.attach_alternative(html_message, 'text/html')
    return mail.send()


def send_tpl_email(template_name, recipient_list, context=None, from_email=None, **kwds):
    t = loader.get_template(template_name)
    c = Context(context or {})
    subject, txt = t.render(c).split("\n", 1)
    from_email = from_email if from_email else settings.DEFAULT_FROM_EMAIL
    headers = {}
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        headers['Template'] = template_name
    return send_mail_with_header(subject=subject.strip(),
                                 message=txt,
                                 from_email=from_email,
                                 recipient_list=recipient_list,
                                 headers=headers,
                                 **kwds)
