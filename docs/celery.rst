Celery - Zadania w tle
======================

Ten dokument opisuje infrastrukturę Celery wdrożoną w projekcie Poradnia w ramach Fazy 1 migracji zadań w tle (Issue #1828).

Przegląd
--------

Celery to system kolejek rozproszonych umożliwiający asynchroniczne wykonywanie zadań w tle. Ta infrastruktura zastępuje starszy system oparty na cron bardziej solidnym i skalowalnym rozwiązaniem.

Architektura
------------

Konfiguracja Celery składa się z trzech głównych komponentów:

1. **RabbitMQ** - Broker wiadomości, który kolejkuje zadania
2. **Celery Worker** - Przetwarza zadania z kolejki
3. **Celery Beat** - Planuje zadania okresowe (zastępuje cron)

Usługi Docker
-------------

RabbitMQ Message Broker
~~~~~~~~~~~~~~~~~~~~~~~~

- **Obraz**: ``rabbitmq:3.12-management-alpine``
- **Porty**:
  - 5672 (protokół AMQP)
  - 15672 (interfejs webowy zarządzania)
- **Dane logowania**: ``poradnia:password`` (tylko dla developmentu)
- **Panel zarządzania**: http://localhost:15672

Celery Worker
~~~~~~~~~~~~~

- Przetwarza zadania w tle asynchronicznie
- Używa tego samego obrazu Docker co usługa web
- Łączy się z RabbitMQ do obsługi kolejki zadań
- Przechowuje wyniki w bazie danych Django

Celery Beat
~~~~~~~~~~~

- Planuje zadania okresowe używając backendu bazodanowego
- Zastępuje stary system cron
- Zadania konfigurowane przez panel administracyjny Django
- Używa ``django-celery-beat`` dla planowania opartego na bazie danych

Konfiguracja
------------

Zależności
~~~~~~~~~~

.. code-block:: text

    celery[rabbitmq]
    django-celery-beat
    django-celery-results

Ustawienia Django
~~~~~~~~~~~~~~~~~~

Ustawienia podstawowe (``config/settings/common.py``)
    Podstawowa konfiguracja Celery współdzielona między środowiskami

Ustawienia deweloperskie (``config/settings/local.py``)
    Połączenie z brokerem localhost, synchroniczne wykonywanie podczas testów

Ustawienia produkcyjne (``config/settings/production.py``)
    Logika ponawiania połączeń, monitorowanie zdarzeń zadań

Zmienne środowiskowe
~~~~~~~~~~~~~~~~~~~~

- ``CELERY_BROKER_URL``: String połączenia z RabbitMQ
- ``CELERY_RESULT_BACKEND``: Backend przechowywania wyników

Polecenia deweloperskie
----------------------

Uruchamianie usług
~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Uruchom wszystkie usługi Celery
    make celery-all

    # Uruchom tylko worker
    make celery-worker

    # Uruchom tylko scheduler beat
    make celery-beat

Monitorowanie i zarządzanie
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Sprawdź status workerów
    make celery-status

    # Wyczyść wszystkie kolejki (używaj ostrożnie)
    make celery-purge

Workflow deweloperski
~~~~~~~~~~~~~~~~~~~~~

1. **Uruchomienie pełnego stosu** (zawiera usługi Celery):

.. code-block:: bash

    make start

2. **Uruchomienie usług Celery osobno**:

.. code-block:: bash

    make celery-all

3. **Monitorowanie zadań** przez interfejs zarządzania RabbitMQ: http://localhost:15672

Tworzenie zadań
---------------

Zadania testowe
~~~~~~~~~~~~~~~

Infrastruktura zawiera dwa zadania testowe do weryfikacji:

.. code-block:: python

    from config.celery import debug_task, test_task

    # Wykonaj zadania testowe
    debug_task.delay()
    test_task.delay("Witaj z Celery!")

Tworzenie nowych zadań
~~~~~~~~~~~~~~~~~~~~~~

Zadania powinny być tworzone w poszczególnych aplikacjach Django używając dekoratora ``@shared_task``:

.. code-block:: python

    # Przykład: poradnia/events/tasks.py
    from celery import shared_task
    from django.core.mail import send_mail

    @shared_task
    def send_event_reminder(event_id):
        # Implementacja zadania
        pass

Integracja z bazą danych
------------------------

Aplikacje Django
~~~~~~~~~~~~~~~~~

Następujące aplikacje są dodane do ``INSTALLED_APPS``:

- ``django_celery_beat`` - Planowanie zadań okresowych
- ``django_celery_results`` - Przechowywanie wyników zadań

Migracje
~~~~~~~~

Uruchom migracje aby utworzyć tabele Celery w bazie danych:

.. code-block:: bash

    docker compose run web python manage.py migrate

Panel administracyjny Django
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Zadania okresowe można konfigurować przez panel administracyjny Django
- Wyniki zadań są widoczne w interfejsie admina
- Zarządzanie harmonogramem Beat przez interfejs webowy
- **Automatyczna synchronizacja**: Wpisy z ``CELERY_BEAT_SCHEDULE`` automatycznie tworzą rekordy w modelu ``PeriodicTask``

Planowanie zadań okresowych
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Istnieją dwa sposoby konfiguracji zadań okresowych:

1. **CELERY_BEAT_SCHEDULE w ustawieniach** (preferowane dla produkcji):

.. code-block:: python

    CELERY_BEAT_SCHEDULE = {
        'nazwa-zadania': {
            'task': 'ścieżka.do.zadania',
            'schedule': 30.0,  # co 30 sekund
            'args': ('arg1', 'arg2'),
            'kwargs': {'kwarg1': 'value1'},
        },
        'zadanie-cron': {
            'task': 'ścieżka.do.zadania',
            'schedule': crontab(hour=12, minute=0),  # codziennie o 12:00
        },
    }

   **Automatyczne tworzenie w bazie danych**: Każdy wpis w ``CELERY_BEAT_SCHEDULE`` automatycznie tworzy odpowiedni rekord ``PeriodicTask`` w bazie danych przy pierwszym uruchomieniu beat scheduler.

2. **Panel administracyjny Django** (dla zmian ad-hoc, tymczasowych, konserwacyjnych):

   - Przejdź do ``/admin/django_celery_beat/``
   - Widzisz wszystkie zadania (z kodu + ręcznie dodane)
   - Możesz modyfikować harmonogramy zadań z ``CELERY_BEAT_SCHEDULE``
   - Dodaj tymczasowe zadania okresowe przez interfejs web
   - Użyj dla jednorazowych zadań konserwacyjnych lub testów

   **Uwaga**: Zmiany zadań z ``CELERY_BEAT_SCHEDULE`` w adminie mogą być nadpisane przy restarcie beat scheduler.

Testowanie
----------

Testowanie deweloperskie
~~~~~~~~~~~~~~~~~~~~~~~~

- Zadania wykonywane natychmiastowo (synchronicznie) gdy ``TESTING=True``
- Używa backendu pamięciowego dla brokera i wyników
- Brak zewnętrznych zależności podczas testów

Testowanie infrastruktury
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Zweryfikuj konfigurację Django
    docker compose run web python manage.py check

    # Testuj import aplikacji Celery
    docker compose run web python -c "from config.celery import app; print('OK')"

    # Testuj wykonanie zadania
    docker compose run web python -c "from config.celery import test_task; print(test_task.delay('test'))"

Monitorowanie
-------------

Interfejs zarządzania RabbitMQ
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Dostęp: http://localhost:15672
- Użytkownik: ``poradnia``
- Hasło: ``password``
- Wyświetlanie kolejek, połączeń i wskaźników wiadomości

Panel administracyjny Django
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Wyniki zadań: ``/admin/django_celery_results/``
- Zadania okresowe: ``/admin/django_celery_beat/``

Logi
~~~~

.. code-block:: bash

    # Logi workerów
    docker compose logs celery-worker

    # Logi beat
    docker compose logs celery-beat

    # Logi RabbitMQ
    docker compose logs rabbitmq

Rozwiązywanie problemów
-----------------------

Częste problemy
~~~~~~~~~~~~~~~

**Worker nie łączy się z brokerem:**

.. code-block:: bash

    # Sprawdź czy RabbitMQ działa
    docker compose ps rabbitmq

    # Sprawdź logi workera
    docker compose logs celery-worker

**Zadania się nie wykonują:**

.. code-block:: bash

    # Sprawdź status workera
    make celery-status

    # Sprawdź kolejki RabbitMQ
    # Odwiedź http://localhost:15672

**Scheduler beat nie działa:**

.. code-block:: bash

    # Sprawdź logi beat
    docker compose logs celery-beat

    # Zweryfikuj istnienie tabel scheduler w bazie danych
    docker compose run web python manage.py dbshell

Kontrole zdrowia
~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Testuj połączenie z brokerem
    docker compose exec celery-worker celery -A config inspect ping

    # Wylistuj aktywne zadania
    docker compose exec celery-worker celery -A config inspect active

    # Sprawdź zarejestrowane zadania
    docker compose exec celery-worker celery -A config inspect registered

Synchronizacja między kodem a bazą danych
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Celery automatycznie synchronizuje wpisy z ``CELERY_BEAT_SCHEDULE`` do modelu ``PeriodicTask``:

- **Przy starcie beat scheduler**: Tworzy rekordy ``PeriodicTask`` dla wszystkich zadań z ``CELERY_BEAT_SCHEDULE``
- **Widoczność w adminie**: Wszystkie zadania (z kodu + ręcznie dodane) widoczne w ``/admin/django_celery_beat/``
- **Modyfikacje w adminie**: Można zmieniać harmonogramy bez edycji kodu
- **Restart scheduler**: Przywraca ustawienia z ``CELERY_BEAT_SCHEDULE`` (nadpisuje zmiany z admina)

Zarządzanie zadaniami w różnych środowiskach
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Development:**
- Przykładowe zadania testowe są włączone w ``CELERY_BEAT_SCHEDULE``
- Automatycznie widoczne w Django admin po uruchomieniu beat
- Zadania wykonywane co 30 sekund i co minutę do testowania infrastruktury

**Production:**
- Zadania produkcyjne zdefiniowane w ``CELERY_BEAT_SCHEDULE``
- Automatycznie synchronizowane do bazy danych
- Widoczne i modyfikowalne przez Django admin

**Dodawanie nowych zadań okresowych:**

1. **Przez kod** (preferowane dla zadań stałych):

   - Dodaj do ``CELERY_BEAT_SCHEDULE`` w ``common.py`` lub ``production.py``
   - Wersjonowane w kodzie, konsystentne między wdrożeniami
   - Automatycznie pojawią się w Django admin po restarcie beat

2. **Przez admin** (dla zadań tymczasowych):

   - Przejdź do ``/admin/django_celery_beat/periodictask/``
   - Kliknij "Add periodic task"
   - Użyj dla zadań konserwacyjnych, testów, jednorazowych operacji
   - Zmiany obowiązują natychmiastowo bez restartu

Migracja z cron
---------------

Ta konfiguracja infrastruktury przygotowuje do migracji istniejących zadań cron:

1. **Aktualne zadania cron** (do migracji w Fazie 2):

   - ``send_event_reminders`` - Codziennie o 12:00
   - ``send_old_cases_reminder`` - Miesięcznie 2. dnia o 06:00
   - ``run_court_session_parser`` - Codziennie o 23:10
   - ``clearsessions`` - Codziennie

2. **Podejście do migracji**:

   - Konwersja poleceń zarządzania na zadania Celery
   - Konfiguracja harmonogramów okresowych w panelu administracyjnym Django
   - Równoległe uruchamianie obu systemów podczas przejścia
   - Usunięcie systemu cron po weryfikacji

Bezpieczeństwo
--------------

Development
~~~~~~~~~~~

- Domyślne dane logowania są zakodowane na stałe dla wygody deweloperskiej
- Interfejs zarządzania RabbitMQ udostępniony tylko na localhost

Produkcja
~~~~~~~~~

- Użyj zmiennych środowiskowych dla wszystkich danych logowania
- Ogranicz dostęp do RabbitMQ do sieci aplikacji
- Rozważ szyfrowanie TLS dla połączeń z brokerem
- Wdróż właściwą autentykację dla interfejsów monitorowania

Następne kroki
--------------

Ta infrastruktura Fazy 1 umożliwia:

1. **Faza 2: Migracja zadań** (Issues #1829-1833)

   - Konwersja istniejących poleceń zarządzania na zadania Celery
   - Konfiguracja harmonogramów okresowych
   - Testowanie równoległego wykonywania z systemem cron

2. **Faza 3: Czyszczenie starego kodu** (Issue #1834)

   - Usunięcie systemu opartego na cron
   - Czyszczenie starych skryptów
   - Finalizacja wdrożenia produkcyjnego

Zobacz także
------------

- `Dokumentacja Celery <https://docs.celeryproject.org/>`_
- `django-celery-beat <https://django-celery-beat.readthedocs.io/>`_
- `django-celery-results <https://django-celery-results.readthedocs.io/>`_
- `Zarządzanie RabbitMQ <https://www.rabbitmq.com/management.html>`_
