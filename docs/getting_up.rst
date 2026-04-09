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

Obrazy Docker w GitHub Container Registry
------------------------------------------

Obrazy Docker aplikacji są dostępne w GitHub Container Registry (GHCR).
Są one automatycznie budowane i publikowane po scaleniu zmian do gałęzi ``master``.

Obraz deweloperski::

    docker pull ghcr.io/watchdogpolska/poradnia/web/dev:latest
    docker pull ghcr.io/watchdogpolska/poradnia/web/dev:<commit_sha>

Obraz produkcyjny::

    docker pull ghcr.io/watchdogpolska/poradnia/web/production:latest
    docker pull ghcr.io/watchdogpolska/poradnia/web/production:<commit_sha>

Tag ``latest`` wskazuje na najnowszą wersję, natomiast tag z hashem commitu
(np. ``a1b2c3d4e5f6...``) umożliwia pobranie konkretnej wersji.

Wdrożenie
---------

Wdrożenie aplikacji odbywa się w sposób typowy dla aplikacji Django z uwzględnieniem standardu 12factory.
