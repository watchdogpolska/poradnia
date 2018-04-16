import re


def clean_text(text):
    return re.sub(r'\s+', ' ', text)


class BaseParser(object):
    signature_rule = None

    def __init__(self, court):
        self.court = court

    def get_session_rows(self):
        return []

    def get_description(self, row):
        return "\n".join("{}:{}".format(key, clean_text(value)) for key, value in sorted(row.items()))
