Cypress
=======

Testy end-to-end wykonywane w środowisku `<cypress.io>`_.

HowTo
=====
Testy najłatwiej wywołać używając pliku docker-compose.test.yml.
Użycie opcji `volumes` sprawia, że pliki zapisane przez Cypress będą widoczne na
maszynie użytkownika. Przydatne w debugowaniu, gdyż Cypress zapisuje pliki wideo
przedstawiające przebieg testów.

.. code-block:: bash
    # polecenie należy wywołać z głównego katalogu repozytorium
    docker-compose --file docker-compose.yml --file docker-compose.test.yml up --build --exit-code-from tests db web tests
