Cypress
=======

Testy end-to-end wykonywane w środowisku `<cypress.io>`_.

HowTo
=====
Jednorazowe wywołanie testów. Użycie flagi `-v` sprawia, że pliki zapisane
przez Cypress będą widoczne na maszynie użytkownika. Przydatne w debugowaniu,
gdyż Cypress zapisuje pliki wideo przedstawiające przebieg testów.

.. code-block:: bash
    docker run -it -v $PWD:/e2e -w /e2e cypress/included:3.2.0
