from django.core import mail


class AssertSendMailMixin:
    @staticmethod
    def _templates_used(email):
        return [
            template
            for template in email.extra_headers["Template"].split("-")
            if email.extra_headers["Template"] and template != "None"
        ]

    def assertSendTemplates(
        self, template_name=None, subject=None, to=None, expected_count=1
    ):
        emails = [
            email
            for email in mail.outbox
            if (template_name and template_name in self._templates_used(email))
            and (not subject or subject in email.subject)
            and (not to or to in email.to)
        ]
        self.assertEqual(
            len(emails),
            expected_count,
            "No mail with template {template_name} and subject {subject} was send to {to}".format(
                template_name=template_name, subject=subject, to=to
            ),
        )
