import logging
from allauth.account.models import EmailAddress
from django.core.management import BaseCommand
from poradnia.users.models import User
from django.db.models import Q, F

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Set verified email address for non spam users"

    def handle(self, **options):
        logger.info("Setting verified email address for non spam users started.")
        # find EmailAddress objects where email does not match associated users
        # email and delete them
        email_addresses_not_matching_users = EmailAddress.objects.filter(
            ~Q(user__email=F("email"))
        )
        logger.info(
            "Email addressesnot matching users count:"
            + f" {email_addresses_not_matching_users.count()}"
        )
        for email in email_addresses_not_matching_users:
            logger.info(f"Email: {email.email}, User: {email.user.email}")
        if email_addresses_not_matching_users.count() > 0:
            start = input("Delete email addresses not matching users (y/n)?")
            if start == "y":
                email_addresses_not_matching_users.delete()
        # fix unverified email addresses for non spam users
        unverified_email_count = User.objects.without_verified_email().count()
        logger.info(f"Unverified email count: {unverified_email_count}")
        verified_email_count = User.objects.with_verified_email().count()
        logger.info(f"Verified email count: {verified_email_count}")
        all_users_count = User.objects.all().count()
        logger.info(f"All users count: {all_users_count}")
        unverified_email_users = User.objects.exclude(
            emailaddress__verified=True,
        )
        unverified_email_users_that_ever_logged_in = unverified_email_users.filter(
            Q(last_login__isnull=False)
        ).distinct()
        logger.info(
            "Unverified email users that ever logged in count:"
            + f" {unverified_email_users_that_ever_logged_in.count()}"
        )
        unverified_email_users_to_set_verified = (
            unverified_email_users_that_ever_logged_in.filter(case_client__isnull=False)
            | unverified_email_users_that_ever_logged_in.filter(
                case_created__isnull=False
            )
            | unverified_email_users_that_ever_logged_in.filter(
                case_modified__isnull=False
            )
            | unverified_email_users_that_ever_logged_in.filter(
                letter_created_by__isnull=False
            )
            | unverified_email_users_that_ever_logged_in.filter(is_staff=True)
            | unverified_email_users_that_ever_logged_in.filter(is_superuser=True)
        )
        logger.info(
            "Unverified email users to set verified count:"
            + f" {unverified_email_users_to_set_verified.count()}"
        )
        unverified_email_users_to_not_set_verified = (
            unverified_email_users_that_ever_logged_in.filter(
                case_client__isnull=True,
                case_created__isnull=True,
                case_modified__isnull=True,
                letter_created_by__isnull=True,
                is_staff=False,
                is_superuser=False,
            )
        )
        logger.info(
            "Unverified email users to not set verified count:"
            + f" {unverified_email_users_to_not_set_verified.count()}"
        )
        if unverified_email_users_to_set_verified.count() > 0:
            start = input("Start the process (y/n)?")
            if start != "y":
                return
            for user in unverified_email_users_to_set_verified:
                email_to_verify, created = EmailAddress.objects.get_or_create(
                    user_id=user.id, email=user.email
                )
                email_to_verify.verified = True
                email_to_verify.save()
                logger.info(
                    f"Verified email address for user {user.email}, created: {created}"
                )
        logger.info("Setting verified email address for non spam users completed.")
