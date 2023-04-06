from datetime import datetime

from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand

from poradnia.letters.models import Letter
from poradnia.letters.utils import get_html_from_eml_file


class Command(BaseCommand):
    help = "Update received letters in database from their emls."

    # def add_arguments(self, parser):
    #     parser.add_argument(
    #         "--monitoring-pk", help="PK of monitoring which receive mail",
    #         required=True
    #     )
    #     parser.add_argument(
    #         "--delete", help="Confirm deletion of email", action="store_true"
    #     )

    def handle(self, *args, **options):
        last_letter = Letter.objects.all().order_by("id").last().id
        start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"Started {start_time}")
        for letter in Letter.objects.all().order_by("id"):
            print(f"Processing letter: {letter.pk} of {last_letter}")
            if not letter.eml or not default_storage.exists(letter.eml.path):
                print(f"Skipping {letter.pk} due to missing eml.")
                continue

            # For easy command debug :)
            #
            # import email
            # from poradnia.letters.utils import get_bytes_from_file
            #
            # eml_content = get_bytes_from_file(letter.eml.file)
            # msg = email.BytesParser(policy=email.policy.default).parsebytes(content)
            # print(50*"=")
            # print('To:', msg['to'])
            # print('From:', msg['from'])
            # print('Subject:', msg['subject'])
            # print(msg['content-type'])
            # print(50*"=")
            # print(msg)
            # print(50*"=")

            letter_html = get_html_from_eml_file(letter.eml.file)
            if letter_html:
                letter.html = letter_html
                letter.save()

        end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"Completed {end_time}")
