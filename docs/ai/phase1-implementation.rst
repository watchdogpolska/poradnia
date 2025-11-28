Plan Implementacyjny - Etap 1
=============================

Przegląd Etapu 1: Indeksowanie Artykułów
-----------------------------------------

Pierwszy etap projektu AI koncentruje się na zbudowaniu solidnych fundamentów technicznych poprzez implementację inteligentnej wyszukiwarki artykułów opartej na technologii embeddings wektorowych. Jest to etap Proof-of-Concept, który pozwoli na walidację podejścia technicznego i zdobycie zaufania prawników.

Cele Biznesowe
~~~~~~~~~~~~~

* **Główny cel**: Umożliwienie prawników szybkiego wyszukiwania relewantnych artykułów i przewodników
* **Cel dodatkowy**: Zbudowanie podstaw technicznych dla kolejnych etapów (precedensy, RAG)
* **ROI**: Redukcja czasu wyszukiwania z 15 minut do 30 sekund
* **Akceptacja**: 80% prawników uznaje system za przydatny

Kryterium Sukcesu
~~~~~~~~~~~~~~~

* **nDCG@10 ≥ 0,8** - jakość wyszukiwania potwierdzona metrykami
* **Czas odpowiedzi < 2 sekundy** - wydajność akceptowalna dla użytkowników
* **99% uptime** - stabilność systemu przez tydzień testów
* **Feedback prawników** - 80% ocen "przydatne" lub wyżej

Architektura Wysokiego Poziomu
------------------------------

.. code-block:: text

   ┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
   │   WordPress     │    │     Crawler      │    │  Text Processor │
   │   REST API      │───▶│                  │───▶│  (BeautifulSoup)│
   └─────────────────┘    └──────────────────┘    └─────────────────┘
                                                            │
                                                            ▼
   ┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
   │ Django Search   │    │   Vector DB      │    │   Embedding     │
   │    Widget       │◀───│                  │◀───│     Model       │
   └─────────────────┘    └──────────────────┘    └─────────────────┘

Składniki Systemu
-----------------

.. list-table:: Komponenty Etapu 1
   :header-rows: 1

   * - Komponent
     - Technologia
     - Lokalizacja
     - Odpowiedzialność
   * - **Źródło Danych**
     - WordPress REST API
     - siecobywatelska.pl
     - Źródło artykułów i metadanych
   * - **Pobieracz**
     - Python + trafilatura
     - Cron/systemd-timer
     - Pobieranie i aktualizacja treści
   * - **Przetwarzanie Tekstu**
     - BeautifulSoup + regex
     - Skrypt Python
     - Czyszczenie i segmentacja tekstu
   * - **Model Embeddingów**
     - sentence-transformers
     - Tylko CPU, lokalnie
     - Generowanie wektorów semantycznych
   * - **Baza Wektorów**
     - MySQL 9.0 VECTOR / Qdrant
     - Istniejąca infrastruktura
     - Przechowywanie embeddingów
   * - **API Wyszukiwania**
     - Django REST Framework
     - Aplikacja Django Poradni
     - Punkt końcowy wyszukiwania
   * - **Widget Interfejsu**
     - Szablony Django + JS
     - Interfejs administracyjny
     - Interfejs użytkownika

Elementy Podlegające Rozwojowi
------------------------------

W trakcie implementacji Etapu 1, następujące komponenty będą rozwijane iteracyjnie:

**Potok Przetwarzania Tekstu**
   * Algorytmy segmentacji - optymalizacja na podstawie jakości wyszukiwania
   * Reguły czyszczenia - dodawanie reguł dla specyficznych formatów
   * Ekstrakcja metadanych - automatyczne tagowanie kategorii

**Strategia Embeddingów**
   * Wybór modelu - testy różnych modeli sentence-transformers
   * Przetwarzanie wstępne - rdzeniowanie, lematyzacja dla języka polskiego
   * Dostrajanie - optymalizacja na polskich tekstach prawnych

**Baza Wektorów**
   * Optymalizacja indeksów - dostrajanie parametrów dla lepszej wydajności
   * Metryki podobieństwa - testowanie kosinusowego vs odległości euklidesowej
   * Strategia skalowania - przygotowanie do większych wolumenów danych

**Algorytm Wyszukiwania**
   * Ulepszenia rankingu - wyszukiwanie hybrydowe (semantyczne + słowa kluczowe)
   * Przetwarzanie zapytań - rozszerzanie, rdzeniowanie, synonimy
   * Filtrowanie wyników - data publikacji, kategoria, źródło

**Interfejs Użytkownika**
   * Doświadczenie wyszukiwania - automatyczne uzupełnianie, sugestie zapytań
   * Prezentacja wyników - fragmenty, podświetlanie, kategoryzacja
   * Punkty integracji - więcej miejsc w interfejsie administracyjnym

**Optymalizacja Wydajności**
   * Strategia buforowania - embeddingi, częste zapytania
   * Przetwarzanie wsadowe - generowanie embeddingów w partiach

Monitorowanie Batch Processing
------------------------------

**Model ProcessingLog**
   Django model do śledzenia wszystkich zadań batch processing

.. code-block:: python

   # knowledge/models.py
   class ProcessingLog(models.Model):
       """Model do monitorowania zadań batch processing"""

       class TaskType(models.TextChoices):
           FETCH_ARTICLES = 'fetch_articles', 'Pobieranie artykułów'
           INDEX_ARTICLES = 'index_articles', 'Indeksowanie artykułów'
           GENERATE_EMBEDDINGS = 'generate_embeddings', 'Generowanie embeddings'
           REINDEX_ALL = 'reindex_all', 'Pełna reindeksacja'
           CLEANUP_ORPHANED = 'cleanup_orphaned', 'Czyszczenie osieroconych rekordów'

       class Status(models.TextChoices):
           RUNNING = 'running', 'W trakcie'
           SUCCESS = 'success', 'Sukces'
           FAILED = 'failed', 'Niepowodzenie'
           PARTIAL = 'partial', 'Częściowy sukces'

       # Podstawowe informacje o zadaniu
       task_type = models.CharField(max_length=50, choices=TaskType.choices)
       status = models.CharField(max_length=20, choices=Status.choices, default=Status.RUNNING)

       # Znaczniki czasowe
       started_at = models.DateTimeField(auto_now_add=True)
       finished_at = models.DateTimeField(null=True, blank=True)

       # Rezultaty i monitoring
       result_data = models.JSONField(
           default=dict,
           help_text="Elastyczne pole na rezultaty (np. {'processed_articles': 42, 'new_embeddings': 156})"
       )

       # Integracja z Sentry dla błędów
       sentry_event_id = models.CharField(max_length=32, null=True, blank=True)

       # Dodatkowe informacje
       log_message = models.TextField(blank=True)
       command_args = models.JSONField(default=dict)

       @property
       def duration(self):
           if self.finished_at:
               return (self.finished_at - self.started_at).total_seconds()
           return None

       def mark_success(self, result_data=None, message=""):
           self.status = self.Status.SUCCESS
           self.finished_at = timezone.now()
           if result_data:
               self.result_data.update(result_data)
           if message:
               self.log_message = message
           self.save()

**Implementacja w Management Commands**

.. code-block:: python

   # knowledge/management/commands/fetch_articles.py
   import sentry_sdk
   from django.core.management.base import BaseCommand
   from knowledge.models import ProcessingLog

   class Command(BaseCommand):
       help = 'Pobieranie nowych artykułów z WordPress API'

       def handle(self, *args, **options):
           # Utworzenie loga przetwarzania
           processing_log = ProcessingLog.objects.create(
               task_type=ProcessingLog.TaskType.FETCH_ARTICLES,
               command_args=options
           )

           try:
               # Pobieranie artykułów
               new_articles = self.fetch_new_articles()
               updated_articles = self.fetch_updated_articles()

               result_data = {
                   'new_articles': len(new_articles),
                   'updated_articles': len(updated_articles),
                   'total_processed': len(new_articles) + len(updated_articles)
               }

               processing_log.mark_success(
                   result_data=result_data,
                   message=f"Pobrano {result_data['total_processed']} artykułów"
               )

               self.stdout.write(
                   self.style.SUCCESS(f'Pobrano {result_data["total_processed"]} artykułów')
               )

           except Exception as e:
               # Integracja z Sentry
               sentry_event_id = sentry_sdk.capture_exception(e)

               processing_log.mark_failed(
                   error_message=str(e),
                   sentry_event_id=sentry_event_id
               )

               self.stdout.write(
                   self.style.ERROR(f'Błąd pobierania artykułów: {e}')
               )
               raise
