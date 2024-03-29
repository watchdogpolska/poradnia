import requests
from lxml import html

from poradnia.judgements.models import SessionRow
from poradnia.judgements.parsers.base import BaseParser
from poradnia.judgements.registry import register_parser


@register_parser("WSA_Gliwice")
class GliwiceETRParser(BaseParser):
    URL = "http://www.gliwice.wsa.gov.pl/56/49/elektroniczny-terminarz-rozpraw-etr.html"
    POST_DATA = {
        "act": "szukaj",
        "data_posiedzenia": "",
        "data_posiedzenia_do": "",
        "guzik": "Filtruj / Sortuj",
        "opis": "",
        "sala_rozpraw": "---",
        "sortowanie": "3",
        "sygnatura": "",
        "symbol": "",
        "wydzial_orzeczniczy": "---",
    }

    def get_content(self):
        response = requests.post(self.URL, data=self.POST_DATA)
        response.raise_for_status()
        return response.text

    def get_session_rows(self):
        content = self.get_content()
        tree = html.document_fromstring(content)
        table = tree.cssselect(".ftabela_123")[0]
        trs = table.cssselect("tr")

        for i in range(0, int(len(trs) / 2)):
            top_tr = trs[i * 2 + 1]
            top_content = [x for x in top_tr.itertext()]
            content = {
                "Wydział orzeczniczy": top_content[0],
                "Sygnatura akt": top_content[1],
                "Data": top_content[2],
                "Godzina": top_content[3],
                "Sala": top_content[4],
                "Organ administracji": top_content[5],
                "Symbol, Przedmiot": "{}: {}".format(top_content[6], top_content[7]),
                "Przewodniczący": top_content[8],
                "Sędziowie": ";".join(top_content[9:]),
            }
            bottom_tr = trs[i * 2 + 2]
            status = bottom_tr.text_content()
            content["Status"] = status
            yield SessionRow(
                signature=content["Sygnatura akt"],
                datetime=self.get_datetime(content),
                description=self.get_description(content),
            )
