from django.conf import settings
from django.core.mail import send_mail
from django.core.management import BaseCommand


class Command(BaseCommand):
    help = "Command that sends test email to app admins."

    def handle(self, *args, **options):
        message_text = f"Hi \n\nThis is test message sent by {settings.APPS_DIR} app\n"
        message_text += "\nFollowing local apps are registered:\n"
        for app in settings.LOCAL_APPS:
            message_text += f"  - {app}\n"
        message_text += f"Test email to app admins sent using {settings.EMAIL_BACKEND}"         
        send_mail(
            subject="Test email from to app admins",
            message=message_text,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[adm[1] for adm in settings.ADMINS],
            fail_silently=False,
        )
        print(f"Test email to app admins sent using {settings.EMAIL_BACKEND}")
