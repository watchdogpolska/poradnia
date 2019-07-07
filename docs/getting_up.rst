Użycie aplikacji
================

Dostępne i aktywnie wspierane są aktualnie dwie metody uruchomienia aplikacji. Starsze oparte o Vagrant
(wspartym przez Ansible) oraz nowsze oparte o Docker.

Praca w środowisku Docker
-------------------------

Obraz przygotowany dla środowiska Docker właściwy jest wyłącznie do pracy w środowisku deweloperskim.

Uruchomienie::

    $ docker-compose build
    $ docker-compose up

Po poprawnym uruchomieniu usług można przejść w przeglądarce pod adres ``http://localhost:8000``.

Warto na początku pracy utworzyć konto administratora poprzez polecenie::

    $ docker-compose run web python manage.py createsuperuser

Wskazane jest także zaimportowanie danych z rejestru TERC poprzez polecenie::

    $ docker-compose run web bash ./.contrib/load_terc.sh

Wdrożenie
---------

Wdrożenie aplikacji odbywa się w sposób typowy dla aplikacji Django z uwzględnieniem standardu 12factory.
