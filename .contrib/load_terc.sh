#!/bin/sh
curl http://cdn.files.jawne.info.pl/private_html/2019_07_peengaiJoo6noo3taiH2shaif2ohru2aiJ3shai8sheesiesei/TERC_Urzedowy_2019-07-07.xml -o /tmp/TERC.xml;
python manage.py load_terc --input /tmp/TERC.xml
