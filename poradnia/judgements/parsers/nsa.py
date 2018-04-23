from datetime import datetime
from time import strptime

import requests
from lxml import html
from pytz import timezone

from ..models import SessionRow
from .base import BaseParser
from ..registry import register_parser


class NSAETRParser(BaseParser):
    URL = 'http://www.nsa.gov.pl/ewokanda/'
    HOUR_FIELD = 'Godz.'
    POST_DATA = {'data': '',
                 'do': '',
                 'kierunek': 'rosnaco',
                 'porzadek': 'termin',
                 'przedmiot': '',
                 'sala': '',
                 'sedzia': '',
                 'sygnatura': '',
                 'symbol': '',
                 'wydzial': ''}

    def get_content(self):
        response = requests.post(self.URL, data=self.POST_DATA)
        response.raise_for_status()
        return response.text

    def get_session_rows(self):
        content = self.get_content()
        tree = html.document_fromstring(content)
        table = tree.cssselect('#tabela')[0]
        header = [th.text_content() for th in table.cssselect('th')]
        for table_row in table[1:]:
            values = [td.text_content() for td in table_row.cssselect('td')]
            content = dict(zip(header, values))
            yield SessionRow(signature=content['Sygnatura'],
                             datetime=self.get_datetime(content),
                             description=self.get_description(content))


register_parser('NSA')(NSAETRParser)


@register_parser('WSA_Bialystok')
class WSABialystokParser(NSAETRParser):
    URL = 'http://www.nsa.gov.pl/ewokanda/wsa/bialystok/'


@register_parser('WSA_Bydgoszcz')
class WSABydgoszczParser(NSAETRParser):
    URL = 'http://www.nsa.gov.pl/ewokanda/wsa/bydgoszcz/'


@register_parser('WSA_Gdansk')
class WSAGdanskParser(NSAETRParser):
    URL = 'http://www.nsa.gov.pl/ewokanda/wsa/gdansk/'


@register_parser('WSA_Gorzow')
class WSAGorzowParser(NSAETRParser):
    URL = 'http://www.nsa.gov.pl/ewokanda/wsa/gorzow/'


@register_parser('WSA_Kielce')
class WSAKielceParser(NSAETRParser):
    URL = 'http://www.nsa.gov.pl/ewokanda/wsa/kielce/'


@register_parser('WSA_Krakow')
class WSAKrakowParser(NSAETRParser):
    # Also http://bip.krakow.wsa.gov.pl/71/177/elektroniczny-terminarz-rozpraw-etr.html
    URL = 'http://www.nsa.gov.pl/ewokanda/wsa/krakow/'


@register_parser('WSA_Lublin')
class WSALublinParser(NSAETRParser):
    URL = 'http://www.nsa.gov.pl/ewokanda/wsa/lublin/'

@register_parser('WSA_Lodz')
class WSALodzParser(NSAETRParser):
    URL = 'http://www.nsa.gov.pl/ewokanda/wsa/lodz/'


@register_parser('WSA_Olsztyn')
class WSAOlsztynParser(NSAETRParser):
    URL = 'http://www.nsa.gov.pl/ewokanda/wsa/olsztyn/'


@register_parser('WSA_Opole')
class WSAOpoleParser(NSAETRParser):
    URL = 'http://www.nsa.gov.pl/ewokanda/wsa/opole/'


@register_parser('WSA_Poznan')
class WSAPoznanParser(NSAETRParser):
    URL = 'http://www.nsa.gov.pl/ewokanda/wsa/poznan/'


@register_parser('WSA_Rzeszow')
class WSARzeszowParser(NSAETRParser):
    URL = 'http://www.nsa.gov.pl/ewokanda/wsa/rzeszow/'


@register_parser('WSA_Szczecin')
class WSASzczecinParser(NSAETRParser):
    URL = 'http://www.nsa.gov.pl/ewokanda/wsa/szczecin/'
