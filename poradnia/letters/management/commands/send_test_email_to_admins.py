from django.conf import settings
from django.core.mail import send_mail
from django.core.management import BaseCommand


class Command(BaseCommand):
    help = "Command that sends test email to app admins."

    def handle(self, *args, **options):
        send_mail(
            subject="Test email to app admins",
            message="Test message content.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=settings.ADMINS,
            fail_silently=False,
        )
        print(f"Test email to app admins sent over {settings.EMAIL_BACKEND}")
