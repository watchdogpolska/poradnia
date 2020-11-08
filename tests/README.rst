Testy end-to-end
================

Testy end-to-end wykonywane są w środowisku `<cypress.io>`_.

HowTo
-----
Testy najłatwiej wywołać używając pliku docker-compose.test.yml lub Makefile.
Użycie opcji `volumes` sprawia, że pliki zapisane przez Cypress będą widoczne na
maszynie użytkownika. Przydatne w debugowaniu, gdyż Cypress zapisuje pliki wideo
przedstawiające przebieg testów.

Debugowanie
-----------
Po każdym wykonaniu, Cypress pozostawia po sobie:

- Pliki wideo z nagraniem przebiegu każdego testu. Znajdują się w folderze cypress/videos.
- Zrzuty ekranu w razie zachowania niezgodnego z oczekiwaniami. Folder cypress/screenshots.

Przy lokalnym wywołaniu testów poprzez docker-compose, pliki widoczne będą na maszynie użytkownika.
Pliki te nie są śledzone przez repozytorium.

Rozbudowa
---------
Kod jest formatowany z użyciem `<prettier.io>`_.

Instalacja::

    $ npm install -g prettier

Aby sformatować plik .js, należy wywołać polecenie::

    $ npx prettier <sciezka_pliku> -w
