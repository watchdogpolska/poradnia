import re

from django.utils.six import text_type


def clean_text(text):
    return re.sub(r'\s+', ' ', text)


class BaseParser(object):
    signature_rule = None

    def __init__(self, court):
        self.court = court

    def get_session_rows(self):
        return []

    def get_description(self, row):
        lines = [text_type("{}: {}").format(key, clean_text(value)) for key, value in sorted(row.items())]
        return text_type("\n").join(lines)
