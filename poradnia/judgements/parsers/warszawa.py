import unicodecsv as csv
from datetime import datetime, timedelta

import requests
from lxml import html

from poradnia.judgements.models import SessionRow
from poradnia.judgements.parsers.base import BaseParser
from poradnia.judgements.registry import register_parser

from io import BytesIO


@register_parser("WSA_Warszawa")
class WarsawETRParser(BaseParser):
    URL = "http://www.warszawa.wsa.gov.pl/183/elektroniczny-terminarz-rozpraw.html"
    # Also http://www.nsa.gov.pl/ewokanda/wsa/warszawa/
    POST_DATA = {
        "act": "szukaj",
        "data_posiedzenia": (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
        "data_posiedzenia_do": "",
        "get_csv": "1",
        "guzik": "Filtruj / Sortuj",
        "sala_rozpraw": "---",
        "sortowanie": "3",
        "typ_posiedzenia": "'N', 'J', 'P'",
        "wydzial_orzeczniczy": "---",
    }

    def get_content(self):
        response = requests.post(self.URL, data=self.POST_DATA)
        response.raise_for_status()
        return response.text

    def fix_dict(self, row):
        return {key.strip(";"): value.strip(";") for key, value in row.items()}

    def get_session_rows(self):
        content = self.get_content()
        tree = html.document_fromstring(content)
        csv_text = tree.cssselect("#csv_text")[0].text_content()
        csv_text = csv_text.encode("utf-8")

        csv_data = csv.DictReader(
            csvfile=BytesIO(csv_text),
            delimiter=" ",
            quotechar="'",
            quoting=csv.QUOTE_ALL,
        )
        csv_data = map(self.fix_dict, csv_data)
        for csv_row in csv_data:
            yield SessionRow(
                signature=csv_row["Sygnatura akt"],
                datetime=self.get_datetime(csv_row),
                description=self.get_description(csv_row),
            )
