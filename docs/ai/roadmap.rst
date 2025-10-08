Roadmapa Projektu AI
====================

Przegląd Etapów Rozwoju
-----------------------

Projekt rozwoju AI dla Poradni Prawnej został podzielony na cztery główne etapy, każdy z jasno określonymi celami biznesowymi i kryteriami sukcesu.

.. list-table:: Harmonogram Wysokiego Poziomu
   :header-rows: 1

   * - Faza
     - Czas trwania
     - Cel biznesowy
     - Kryterium "gotowe"
   * - **0. Discovery**
     - Potwierdzić potrzeby prawników i ryzyka RODO
     - Podpisany DPIA + architektura 1-slajd
   * - **1. Proof-of-Concept**
     - Wyszukiwarka artykułów z wektorami
     - nDCG@10 ≥ 0,8; prawnicy "tak, trafia"
   * - **2. Pilot**
     - 3-4 miesiące
     - Integracja z Poradnią, manualne linkowanie
     - ≥ 60% odpowiedzi z linkiem
   * - **3. MVP RAG**
        - Szkic odpowiedzi dla 1 kategorii spraw
     - 80% szkiców < 20% poprawek

Faza 0: Discovery (2-4 tygodnie)
--------------------------------

Cele
~~~~

* Zweryfikowanie potrzeb prawników i ich gotowości do korzystania z AI
* Analiza ryzyk związanych z RODO i ochroną danych
* Wybór dostawcy chmury (Azure/AWS/GCP)
* Przygotowanie dokumentacji technicznej i prawnej

Kluczowe Działania
~~~~~~~~~~~~~~~~~~

**Analiza potrzeb**
   * Wywiady z interesariuszami
   * Analiza istniejących procesów odpowiadania na zapytania
   * Identyfikacja najczęstszych typów spraw
   * Mapowanie źródeł wiedzy (artykuły, precedensy, przepisy)

**Analiza prawna i techniczna**
   * Przygotowanie Data Protection Impact Assessment (DPIA)
   * Analiza zgodności z RODO
   * Wybór regionu i dostawcy usług chmurowych
   * Architektura wysokiego poziomu

**Planowanie implementacji**
   * Szczegółowy backlog dla fazy PoC
   * Podział na "MVP" i "nice-to-have"
   * Estymacja kosztów i zasobów (w tym LLM)
   * Plan testów i walidacji

Dostarczane Produkty
~~~~~~~~~~~~~~~~~~~

* **DPIA** - ocena wpływu na ochronę danych osobowych
* **Architektura systemu** - diagram jednej strony z komponentami
* **Backlog produktowy** - user stories dla fazy PoC
* **Umowa z dostawcą chmury** - zgodna z RODO

Kryterium Sukcesu
~~~~~~~~~~~~~~~~

* Podpisany DPIA zaakceptowany przez prawników
* Wybrana platforma chmurowa (Azure/AWS) z prywatnymi endpointami
* Potwierdzenie przydatności rozwiązania przez minimum 80% prawników

Faza 1: Proof-of-Concept
---------------------------------------

Cele
~~~~

* Zbudowanie funkcjonalnej wyszukiwarki artykułów opartej na embeddings
* Walidacja jakości wyszukiwania z prawnikami
* Przygotowanie fundamentów technicznych dla kolejnych faz

Zakres Funkcjonalny
~~~~~~~~~~~~~~~~~~

**Indeksowanie treści**
   * Crawler dla artykułów z siecobywatelska.pl
   * Ekstrakcja tekstu z HTML i PDF
   * Chunking treści na fragmenty ~500 tokenów
   * Generowanie embeddings (paraphrase-multilingual-mpnet-base-v2)

**Baza wektorowa**
   * MySQL 9.0 z kolumnami VECTOR lub Qdrant w Docker
   * Metadane: URL, data publikacji, kategoria, tagi
   * API wyszukiwania similarity search

**Interfejs użytkownika**
   * Prosta wyszukiwarka w Django admin
   * Endpoint REST API /search?q=
   * Wyniki z linkami do źródeł i fragmentami tekstu

Architektura Techniczna
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

   [WordPress API] → [Crawler/Trafilatura] → [Text Processing]
                                                     ↓
   [Django Admin Search] ← [Vector DB] ← [Embedding Model]

**Komponenty**
   * **Crawler**: skrypt Python z trafilatura/BeautifulSoup
   * **Embedding**: sentence-transformers (CPU-only) lub LLM provider (np. Azure OpenAI)
   * **Vector DB**: MySQL VECTOR lub Qdrant (single binary)
   * **API**: nowa Django app "knowledge"

Proces Walidacji
~~~~~~~~~~~~~~~~

**Testy techniczne**
   * Czas odpowiedzi < 2 sekundy
   * Stabilność systemu przy 100 zapytaniach/minutę

**Testy z prawnikami**
   * 20 zapytań testowych od prawników
   * Ocena relevantności wyników (skala 1-5)
   * Porównanie z obecnym sposobem wyszukiwania

Harmonogram
~~~~~~~~~~

**Podfaza 1**
   * Setup infrastruktury i crawlera
   * Implementacja embeddings i vector DB

**Podfaza 2**
   * Interfejs wyszukiwania w widoku sprawy
   * Testy i optymalizacja

**Podfaza 3**
   * Walidacja z prawnikami
   * Poprawki i przygotowanie do pilotu

Kryterium Sukcesu
~~~~~~~~~~~~~~~~

* **nDCG@10 ≥ 0,8** - metryka jakości wyszukiwania
* **Akceptacja prawników** - minimum 80% ocen "przydatne" lub "bardzo przydatne"
* **Wydajność** - obsługa 50 użytkowników jednocześnie
* **Stabilność** - 99% uptime przez tydzień testów

Faza 2: Pilot
----------------------------

Cele
~~~~

* Integracja wyszukiwarki z istniejącym systemem Poradni
* Rozszerzenie na bazę precedensów (istniejące sprawy)
* Implementacja manualnego linkowania podobnych spraw

Nowe Funkcjonalności
~~~~~~~~~~~~~~~~~~~

**Integracja z systemem Poradni**
   * Widget wyszukiwania w interfejsie obsługi spraw
   * Automatyczne sugerowanie artykułów na podstawie pytania klienta
   * Możliwość dodawania linków do odpowiedzi

**Indeksowanie precedensów**
   * Sanityzacja danych osobowych z istniejących spraw
   * Embeddings dla pytań i odpowiedzi klientów (z 2015 r.)
   * Osobna przestrzeń wektorowa lub wspólna z artykułami

**Funkcje dla prawników**
   * "Znajdź podobne sprawy" - button w interfejsie sprawy
   * Historia wyszukań prawnika
   * Bookmarki i notatki do artykułów

Architektura Rozszerzona
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

   [Django Poradnia]
           ↓
   [Knowledge Widget] ← [Search API] ← [Vector DB]
           ↓                               ↑
   [Case Similarity]                [Legacy Cases]
           ↓                               ↑
   [Response Templates]           [Article Index]

Bezpieczeństwo i RODO
~~~~~~~~~~~~~~~~~~~~

**Pseudonimizacja danych (do potwierdzenia)**
   * Automatyczne usuwanie imion, nazwisk, PESEL
   * Zastępowanie placeholderami: [IMIĘ], [FIRMA], [ADRES]
   * Haszowanie identyfikatorów dla zapewnienia spójności

**Kontrola dostępu**
   * Tylko zalogowani prawnicy mają dostęp do precedensów
   * Logi dostępu zgodnie z art. 30 RODO
   * Możliwość wykluczenia wrażliwych spraw lub klientów z indeksu

Proces Pilotażu
~~~~~~~~~~~~~~

**Podfaza 1 **
   * Wdrożenie u 2-3 prawników
   * Integracja z 10% istniejących spraw
   * Dzienne zbieranie feedbacku

**Podfaza 2**
   * Rozszerzenie na cały zespół prawników
   * Indeksowanie wszystkich przypadków od 2020 r.
   * Optymalizacja na podstawie użytkowania

**Podfaza 3**
   * Pełna integracja z systemem
   * Wszystkie sprawy w indeksie (po sanityzacji)
   * Szkolenie prawników z nowych funkcji

Metryki Sukcesu
~~~~~~~~~~~~~~

* **≥ 60% odpowiedzi zawiera link** do artykułu z podpowiedzi
* **Czas wyszukiwania** - średnio 5 sekund zamiast 15 minut
* **Użycie dzienne** - każdy prawnik wykonuje minimum 10 wyszukań
* **Satysfakcja** - 85% prawników ocenia system jako przydatny

Faza 3: MVP RAG
------------------------------

Cele
~~~~

* Implementacja automatycznego generowania szkiców odpowiedzi
* System RAG (Retrieval-Augmented Generation)
* Human-in-the-loop workflow z możliwością edycji i zatwierdzenia

Funkcjonalności RAG
~~~~~~~~~~~~~~~~~~

**Pipeline generowania szkiców**
   1. Analiza nowego pytania klienta
   2. Wyszukiwanie top-k artykułów i precedensów
   3. Generowanie szkicu odpowiedzi przez LLM
   4. Prezentacja prawnikowi do edycji
   5. Zatwierdzenie i wysłanie odpowiedzi

**Integracja z LLM**
   * Wykorzystanie europejskiego dostawcy LLM np. Azure OpenAI GPT-4o w europopejskim regionie
   * Prywatne endpointy dla bezpieczeństwa
   * Brak trenowania na danych klienta

**Kontrola jakości**
   * Wymuszenie cytowania źródeł w odpowiedzi
   * Filtry anty-halucynacyjne
   * Feedback loop - "zaakceptowano/zmieniono"

Architektura RAG
~~~~~~~~~~~~~~~

.. code-block:: text

   [Nowe pytanie] → [Chunking + Classification]
                           ↓
   [Retrieval] → [Top-k articles + cases] → [LLM Prompt]
                           ↓                      ↓
   [Generated Draft] ← [Azure OpenAI] ← [Context + Templates]
                           ↓
   [Lawyer Review] → [Edit/Approve] → [Send Response]
                           ↓
                    [Feedback Loop]

Prompty i Szablony
~~~~~~~~~~~~~~~~~

**System prompt**
   * Rola: ekspert prawa administracyjnego
   * Zadanie: szkic odpowiedzi na pytanie o dostęp do informacji
   * Wymagania: cytowanie źródeł, struktura odpowiedzi
   * Ograniczenia: nie udzielaj porad w sprawach karnych

**Template odpowiedzi**
   * Wprowadzenie i powitanie
   * Analiza prawna z cytowaniem przepisów
   * Rekomendacje praktyczne
   * Linkowane źródła i precedensy
   * Informacje kontaktowe

Testy i Walidacja
~~~~~~~~~~~~~~~~

**Metryki jakości**
   * **Precyzja cytowań** - czy linkowane źródła są relevantne
   * **Kompletność** - czy szkic zawiera wszystkie istotne aspekty
   * **Poprawność prawna** - weryfikacja przez prawników
   * **Użyteczność** - czas edycji vs generowania od zera

**Proces testowy**
   * Zestaw 50 reprezentatywnych pytań
   * Generowanie szkiców przez AI vs przygotowanie manualne
   * Ślepa ocena przez prawników (bez informacji o źródle)
   * A/B testing z prawnikami

Harmonogram Fazy 3
~~~~~~~~~~~~~~~~~

**Podfaza 1: Przygotowanie**
   * Implementacja integracji z Azure OpenAI
   * Rozwój promptów i szablonów
   * Przygotowanie zestawu testowego

**Podfaza 2: Implementacja**
   * Pipeline RAG end-to-end
   * Interfejs do edycji szkiców
   * System feedback i logowania

**Podfaza 3: Testy i optymalizacja**
   * Testy z prawnikami
   * Optymalizacja promptów
   * Przygotowanie do wdrożenia produkcyjnego

Kryterium Sukcesu
~~~~~~~~~~~~~~~~

* **80% szkiców wymaga mniej niż 20% poprawek**
* **Czas przygotowania odpowiedzi** - redukcja o 60%
* **Jakość prawna** - 95% szkiców bez błędów merytorycznych
* **Akceptacja prawników** - 90% chce korzystać z systemu regularnie

Zaawansowane Funkcje (Faza 4+)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* **Predykcja wyników** - oszacowanie szans powodzenia sprawy
* **Automatyczne dokumenty** - generowanie pism procesowych
* **Analytics** - statystyki i trendy w sprawach

Monitoring i Utrzymanie
-----------------------

Metryki Operacyjne
~~~~~~~~~~~~~~~~~

* **Monitoring kosztu** - miesięczne raporty kosztów LLM

Zgodność
~~~~~~~~~~~~~~~~~

* **Logi dostępu** - kto, kiedy, do jakich danych
* **Backup** - dzienny backup embeddings i metadanych
* **zgodnosć GDPR ** - stała współpraca z prawnikami

Rozwój Zespołu
~~~~~~~~~~~~~~

* **Szkolenia AI** - dla prawników i developerów
* **Best practices** - dokumentacja procesów
* **Społeczność (Community)** - udział w konferencjach prawno-technologicznych
