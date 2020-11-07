Testy end-to-end
================

Testy end-to-end wykonywane są w środowisku `<cypress.io>`_.

HowTo
-----
Testy najłatwiej wywołać używając pliku docker-compose.test.yml lub Makefile.
Użycie opcji `volumes` sprawia, że pliki zapisane przez Cypress będą widoczne na
maszynie użytkownika. Przydatne w debugowaniu, gdyż Cypress zapisuje pliki wideo
przedstawiające przebieg testów.

Rozbudowa
---------
Kod jest formatowany z użyciem `<prettier.io>`_.

Instalacja::

    $ npm install -g prettier

Aby sformatować plik .js, należy wywołać polecenie::

    $ npx prettier <sciezka_pliku> -w
