Keys
======

Wdrożony został moduł kluczy dostępu. Zapewnia on kontrolę dostępu do treści przeznaczonych dla konkretnego  użytkownika w przypadku dostępu maszynowego. Umożliwia on uzyskanie dostępu do treści bez ujawniania hasła użytkownika.

Moduł rejestruje dane w zakresie:
* czasu ostatniego użycia klucza,
* czasu pobrania klucza z aplikacji,
* etykiety klucza

Treści o dostępie maszynowym
----------------------------

Tylko do wybranych treści dostęp możliwy jest z wykorzystaniem kluczy dostępu. Z strony programistycznej są to treści wykorzystujące ```keys.mixins.KeyAuthMixin```, co w praktyce oznacza ([szukaj w kodzie](https://github.com/watchdogpolska/poradnia/search?utf8=%E2%9C%93&q=KeyAuthMixin)):
* widok kalendarza w formacie - ```/event/ical/```.

Logowanie
---------

Aby uzyskać treści należy przekazać dane autoryzacyjne przy każdym żądaniu. Można to zrobić poprzez:
* dane HTTPAuth Basic - ```//{{username}}}:{{key}}}@example.com/event/ical```
* dane GET - ```//example.com/event/ical?username={{username}}&key={{key}}```

Kod aplikacji
-------------

Model
######
.. automodule:: poradnia.keys.models
    :members:

Widoki
######
.. automodule:: poradnia.keys.views
    :members:

Formularze
##########
.. automodule:: poradnia.keys.forms
    :members:
