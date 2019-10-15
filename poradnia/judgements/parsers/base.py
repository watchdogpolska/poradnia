import logging
import re
from datetime import datetime
from time import strptime

from pytz import timezone


def clean_text(text):
    return re.sub(r'\s+', ' ', text)


logger = logging.getLogger(__name__)


class BaseParser(object):
    signature_rule = None
    DATE_FIELD = 'Data'
    HOUR_FIELD = 'Godzina'

    def __init__(self, court):
        self.court = court

    def get_session_rows(self):
        return []

    def get_description(self, row):
        lines = ["{}: {}".format(key, clean_text(value)) for key, value in sorted(row.items())]
        return "\n".join(lines)

    def get_datetime(self, row):
        if self.HOUR_FIELD in row and not row[self.HOUR_FIELD]:
            return self.get_date(row)

        try:
            struct = strptime("{} {}".format(row[self.DATE_FIELD], row[self.HOUR_FIELD]), "%Y-%m-%d %H:%M")
            return datetime(*struct[:6]).replace(tzinfo=timezone('Europe/Warsaw'))
        except ValueError:
            print(row)
            return self.get_date(row)
        except KeyError:
            msg = "Invalid headers in {}".format(self.__class__.__name__)
            print(msg)
            print(row)
            logger.warning(msg)
            return self.get_date(row)

    def get_date(self, row):
        struct = strptime(row[self.DATE_FIELD], "%Y-%m-%d")
        return datetime(*struct[:6]).replace(tzinfo=timezone('Europe/Warsaw'), hour=0, minute=0, second=0)
