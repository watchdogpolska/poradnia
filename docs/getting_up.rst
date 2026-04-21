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

Praca z VSCode (debugowanie)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Dla deweloperów korzystających z VSCode dostępny jest plik nadpisujący konfigurację Docker
(``docker-compose.vscode.yml``), który pozwala uruchomić serwer Django z poziomu edytora
w trybie debugowania.

W tym trybie kontener ``web`` uruchamia się, wykonuje migracje, a następnie oczekuje na
ręczne uruchomienie serwera przez VSCode — zamiast startować ``runserver`` automatycznie.

**Opcja 1 — flaga ``-f`` (jednorazowo w danym wywołaniu):**

.. code-block:: bash

    $ docker-compose -f docker-compose.yml -f docker-compose.vscode.yml up

**Opcja 2 — zmienna środowiskowa ``COMPOSE_FILE`` w bieżącej sesji powłoki:**

.. code-block:: bash

    $ export COMPOSE_FILE=docker-compose.yml:docker-compose.vscode.yml
    $ docker-compose up

**Opcja 3 — trwale przez plik ``.env`` (zalecane dla codziennej pracy):**

Dodaj zmienną do pliku ``.env`` w katalogu projektu:

.. code-block:: bash

    $ echo "COMPOSE_FILE=docker-compose.yml:docker-compose.vscode.yml" >> .env

Następnie wystarczy standardowe polecenie::

    $ docker-compose up

.. note::
   Plik ``.env`` jest ignorowany przez Git, więc ustawienie to jest lokalne
   i nie wpływa na innych deweloperów.

Po uruchomieniu kontenerów użyj konfiguracji uruchamiania VSCode (``launch.json``),
aby wystartować i debugować serwer Django wewnątrz kontenera.

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
