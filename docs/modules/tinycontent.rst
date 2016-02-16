django-tinycontent
==================


Aplikacja została wyposażona w moduł sekcji edycyjnych. Moduł
wykorzystuje ``dominicrodger/django-tinycontent``.

Zdefiniowane sekcje
-------------------

Istnieją następujące zdefiniowane sekcje edycyjne: 

- ``./templates/pages/home.html``:

  - ``home:start`` - początkowa część strony głównej, która jest dostępna dla każdego i wyświetlana każdemu 
  - ``home:anonymous`` - część strony głównej, która jest wyświetlana dla osoby niezalogowanej 
  - ``home:user`` - część strony głównej, która jest wyświetlana dla osoby zalogowanej 

- ``./templates/base.html``: 

  - ``footer`` - stopka strony 

- ``./letters/templates/letters/form_new.html``: 

  - ``letters:new_case_up`` - opis formularza nowej sprawy 

- ``./utilities/forms.py``: 

  - ``giodo`` - opis pola wyrażenia zgody na przetwarzanie danych osobowych
