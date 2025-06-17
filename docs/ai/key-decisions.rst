Kluczowe Decyzje Projektowe
===========================

Przed rozpoczęciem implementacji projektu AI dla Poradni Prawnej konieczne jest podjęcie szeregu strategicznych decyzji technicznych i biznesowych. Niniejszy dokument przedstawia najważniejsze wybory, ich konsekwencje oraz rekomendacje uwzględniające ograniczone zasoby zespołu i brak AI jako kluczowej funkcjonalności.

⚠️ **Założenia projektu**
   * AI może być wyłączony - nie jest kluczową funkcjonalnością
   * Ograniczone zasoby zespołu deweloperskiego
   * Przestarzała MySQL bez wsparcia vector search
   * Preferowane batch processing nad real-time

Decyzje Strategiczne (Wymagają zatwierdzenia kierownictwa)
--------------------------------------------------------

1. Wybór Dostawcy Chmury
~~~~~~~~~~~~~~~~~~~~~~~

**Kontekst decyzji**
   Zgodność z RODO wymaga wykorzystania dostawców chmury oferujących regiony europejskie i gwarancje nieprzenoszenia danych poza EOG.

**Opcje**

.. list-table:: Porównanie Dostawców Chmury
   :header-rows: 1

   * - Kryteria
     - **Azure** (rekomendacja)
     - **AWS**
     - **Google Cloud**
   * - **Regiony EOG**
     - ✅ North Europe, West Europe
     - ✅ eu-central-1, eu-west-1
     - ✅ europe-west1, europe-west4
   * - **OpenAI GPT-4**
     - ✅ Azure OpenAI Service
     - ❌ Brak bezpośredniej integracji
     - ❌ Brak bezpośredniej integracji
   * - **RODO Compliance**
     - ✅ Data Zones EU
     - ✅ Private endpoints
     - ✅ Private endpoints
   * - **Koszty LLM**
     - €€ Średnie
     - €€€ Wysokie (Bedrock)
     - €€ Średnie (Vertex AI)
   * - **Doświadczenie zespołu**
     - ⚠️ Ograniczone
     - ⚠️ Ograniczone
     - ⚠️ Ograniczone

**Rekomendacja**: Azure ze względu na Azure OpenAI Service i Data Zones EU

**Konsekwencje wyboru**
   * Azure: Natywna integracja z GPT-4, ale wyższe koszty infrastruktury
   * AWS: Bedrock Claude/Mistral, ale wyższe koszty API
   * Google: Vertex AI, ale brak GPT-4, własne modele (PaLM)

**Wymagane działania**
   * Negocjacja umowy DPA z wybranym dostawcą
   * Przeszkolenie zespołu z wybranej platformy

1a. Azure-Native Architecture Alternative
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Kontekst rozważań**
   Przy wyborze Azure jako preferowanego dostawcy chmury, istnieją dedykowane Azure-native rozwiązania, które mogą uprościć architekturę i zmniejszyć ilość kodu do zarządzania przez zespół.

**Azure-oriented Ingestion Tracks**

.. list-table:: Gotowe Stosy Ingestion w Azure
   :header-rows: 1

   * - Track
     - Co daje gotowe
     - Jak to działa technicznie
     - Typowe wywołania Python SDK
   * - **A. Azure AI Search + Integrated Vectorization**
     - Ingestion w jednym kroku → tekst i PDF, chunking, embeddings i zapis do indeksu wektorowego
     - **Data Source** (Blob/WP export) → **Indexer** → **Skillset** z Document Cracking + Azure OpenAI Embedding Skill → **Vector field**
     - ``azure-search-documents`` → ``SearchIndexerClient.create_indexer()`` → query via ``VectorQuery``
   * - **B. Document Intelligence → Search**
     - Wysokiej jakości OCR/layout parsing dla PDF przed wektoryzacją
     - **DocumentIntelligenceClient** → model ``prebuilt-layout`` → paragraphs → skrypt dzieli i embeddings → **Push API** do Search
     - ``azure-ai-documentintelligence`` → ``begin_analyze_document("prebuilt-layout")`` → iterate ``paragraph.content``
   * - **C. Azure OpenAI "On Your Data"**
     - Pełnozarządzany RAG store (ingestion, chunking, embeddings, obsługa cytowań) za jednym endpointem ``/chat/completions``
     - Rejestracja **Azure AI Search** indeksu jako ``data_source`` → service auto-uruchamia indexers & chunking
     - ``openai.AzureOpenAI().chat.completions.create(…, extra_body={"data_sources":[{"type":"azure_search", …}]})``
   * - **D. LangChain/LlamaIndex na Azure AI Search**
     - Te same ergonomiczne loadery/splittery, ale wektory w Azure AI Search
     - Loader → ``CharacterTextSplitter`` → ``AzureAISearchVectorStore`` (auto-tworzy indeks, obsługuje batch, hybrid search)
     - ``langchain.vectorstores.azuresearch.AzureSearch.add_documents(docs)`` → ``similarity_search()``

**Architektura Azure-Native w dwu-VM setup**

.. code-block:: text

   [WordPress REST API] →[JSON]→ [PullScript]
   [Azure Blob] ← [attachments] ← [PullScript]
                ↓
   [Azure AI Search Indexer] ← [optional OCR] ← [Document Intelligence]
                ↓
   [Integrated Vectorization] → [Azure AI Search Index]
                ↓
   [Django Knowledge App] ← [Azure AI Search SDK]

**Komponenty**:
   * **PullScript** - 50-liniowy skrypt Python: ``GET /wp-json/wp/v2/posts?after=<timestamp>`` → zapis do Blob
   * **Indexer** - zdefiniowany raz w Azure portal lub via ``SearchIndexerClient`` → harmonogram co 6h
   * **Document Intelligence (opcjonalnie)** - tylko dla nowych PDF → zwraca Markdown/tekst
   * **EmbedStep** - Track A: integrated vectorization LUB Track B/D: własny ``SentenceTransformer``/``OpenAIEmbedding``
   * **VectorSink** - Azure AI Search indeks z ``chunks`` (text) + ``chunk_vector`` (FLOAT_VECTOR(1536))

**Zalety Azure-native approach**:
   * **Built-in chunking & retry logic** - Integrated vectorization obsługuje token limits i batching
   * **First-class PDF support** - Document Intelligence rozumie layout, tabele, pismo odręczne
   * **End-to-end RAG z cytowaniami** - "On Your Data" opakowuje retrieval + re-ranking + GPT-4o za jednym requestem
   * **Framework ecosystem** - LangChain/LlamaIndex adaptery = można później zamienić na lokalne modele

**Wady Azure-native approach**:
   * **Vendor lock-in** - silniejsze uzależnienie od Azure niż obecna rekomendacja
   * **Mniejsza kontrola** - mniej możliwości fine-tuningu pipeline'u
   * **Koszty** - potencjalnie wyższe koszty niż Qdrant Cloud + OpenAI API
   * **Learning curve** - zespół musi opanować Azure AI Search zamiast prostszego Qdrant

**Quick start snippet (Track A)**

.. code-block:: python

   from azure.identity import DefaultAzureCredential
   from azure.search.documents.indexes import SearchIndexerClient

   creds = DefaultAzureCredential()
   svc = "https://<search>.search.windows.net"
   admin = SearchIndexerClient(endpoint=svc, credential=creds)

   # 1. blob → datasource
   # 2. skillset includes `azureOpenAiSkill` referencing embedding deployment
   # 3. index defines `content_vec` : Collection(Edm.Single) dimensions=1536
   # 4. indexer wires it together
   admin.create_indexer(indexer)          # one-time
   admin.run_indexer(indexer.name)        # ad-hoc or via scheduledFrequency

**Wybór właściwego track'u**

.. list-table:: Rekomendacje Azure Tracks
   :header-rows: 1

   * - Jeśli chcesz...
     - Zacznij od
   * - **zero ingestion code**
     - **A** lub **C**
   * - **fine OCR/table accuracy**
     - dodaj **B**
   * - **framework glue & future portability**
     - warstwa **D** na górze

**⚠️ Rekomendacja zespołu**: **Zachować obecną rekomendację Qdrant Cloud + OpenAI API**

**Uzasadnienie**:
   * **Prostota implementacji** - mniej komponentów Azure do nauki
   * **Vendor portability** - łatwiejsza migracja między dostawcami w przyszłości
   * **Kontrola kosztów** - lepsze monitorowanie kosztów przy dedykowanych serwisach
   * **Debugging** - prostsze debugowanie własnego pipeline'u
   * **Zespół AI-beginner friendly** - Azure AI Search wymaga głębszej znajomości Azure ekosystemu

**Kiedy rozważyć Azure-native**:
   * **Zespół posiada Azure expertise**
   * **Projekt jest Azure-first** (nie tylko AI komponenty)
   * **Wymagane zaawansowane PDF processing** (Document Intelligence)
   * **Planowany rapid scaling** (>100k artykułów)

2. Model Embedding - API vs Self-hosted
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Kontekst decyzji**
   Wybór między zewnętrznymi API a self-hosted modelami wpływa na koszty, latencję i niezależność technologiczną.

**Opcje A: Zewnętrzne API**

.. list-table:: Dostawcy API Embedding
   :header-rows: 1

   * - Dostawca
     - **OpenAI** (rekomendacja)
     - **Cohere**
     - **Voyage AI**
   * - **Model**
     - text-embedding-3-small
     - embed-multilingual-v3.0
     - voyage-large-2
   * - **Wymiary**
     - 1536
     - 1024
     - 1536
   * - **Koszty/1M tokenów**
     - $0.02 (€0.018)
     - $0.10 (€0.09)
     - $0.12 (€0.11)
   * - **Język polski**
     - ✅ Bardzo dobry
     - ✅ Natywny multilingual
     - ⚠️ Dobry
   * - **RODO compliance**
     - ⚠️ Wymaga DPA
     - ⚠️ Wymaga DPA
     - ⚠️ Wymaga DPA

**Oszacowanie kosztów:**
   * Ocenić ilość artykułów do indeksowania
   * Ocenić szacunkową ilość tokenów
   * Oszacować koszt embeddingów w zależności od wybranego dostawcy dla początkowego indeksowania i miesięcznego użycia

**Opcje B: Self-hosted**

.. list-table:: Modele Self-hosted
   :header-rows: 1

   * - Model
     - **sentence-transformers/paraphrase-multilingual-mpnet-base-v2**
     - **intfloat/multilingual-e5-large**
     - **KLUCBERT-PL**
   * - **Wsparcie PL**
     - ✅ Bardzo dobre
     - ✅ Bardzo dobre
     - ✅ Natywne polskie
   * - **Rozmiar modelu**
     - 420MB
     - 2.24GB
     - 500MB
   * - **Wymiary**
     - 768
     - 1024
     - 768
   * - **Wymagania GPU**
     - ❌ CPU sufficient
     - ⚠️ GPU rekomendowane
     - ❌ CPU sufficient
   * - **Koszty miesięczne**
     - €0 (existing infra)
     - €50-100 (GPU instance)
     - €0 (existing infra)

**Rekomendacja**: **OpenAI API** dla zespołów z ograniczonymi zasobami

**Uzasadnienie**:
   * Brak potrzeby zarządzania infrastrukturą ML
   * Przewidywalne koszty (~€30-50/miesiąc)
   * Wysoka jakość dla języka polskiego
   * Łatwa migracja do self-hosted w przyszłości

3. Baza Wektorowa - SaaS vs Self-hosted
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Kontekst decyzji**
   Przestarzała MySQL bez wsparcia vector search wymaga alternatywnego rozwiązania.

**Opcje A: SaaS Vector Databases**

.. list-table:: SaaS Vector Databases
   :header-rows: 1

   * - Rozwiązanie
     - **Pinecone**
     - **Qdrant Cloud**
     - **Weaviate Cloud**
   * - **Starter plan**
     - Free tier (2GB)
     - Free tier (1GB)
     - Free tier (14 dni)
   * - **Produkcja/miesiąc**
     - €70 (Standard)
     - €19 (1GB cluster)
     - €22 (Standard)
   * - **Koszty storage/GB**
     - €25/GB/miesiąc
     - €14/GB/miesiąc
     - €20/GB/miesiąc
   * - **Zarządzanie**
     - ✅ Fully managed
     - ✅ Fully managed
     - ✅ Fully managed
   * - **RODO compliance**
     - ✅ EU regions
     - ✅ EU regions
     - ✅ EU regions
   * - **Vendor lock-in**
     - ⚠️ Proprietary API
     - ✅ Open source Qdrant
     - ✅ Open source Weaviate

**Oszacowanie kosztów dla 10,000 artykułów:**
   * Każdy artykuł: ~3 chunki po 1536 wymiarów (OpenAI)
   * Całkowity storage: ~180MB embeddings
   * **Pinecone**: €70/miesiąc (1GB plan)
   * **Qdrant Cloud**: €19/miesiąc (1GB plan)
   * **Weaviate Cloud**: €22/miesiąc (Standard)

**Opcje B: Self-hosted**

.. list-table:: Self-hosted Vector Databases
   :header-rows: 1

   * - Rozwiązanie
     - **Qdrant**
     - **Weaviate**
     - **ChromaDB**
   * - **Deployment**
     - Docker/Binary
     - Docker/Kubernetes
     - Python package
   * - **Operacyjne maintenance**
     - ⚠️ Średnie
     - ⚠️ Wysokie
     - ✅ Minimalne
   * - **Wydajność**
     - ✅ Bardzo wysoka
     - ✅ Wysoka
     - ⚠️ Średnia
   * - **Skalowalność**
     - ✅ Horizontal
     - ✅ Horizontal
     - ⚠️ Single node
   * - **Koszty hosting**
     - €20-40/miesiąc
     - €40-80/miesiąc
     - €10-20/miesiąc

**Rekomendacja**: **Qdrant Cloud** dla zespołów z ograniczonymi zasobami

**Uzasadnienie**:
   * Najniższe koszty SaaS (€19/miesiąc)
   * Brak vendor lock-in (open source)
   * Automatyczne backup i monitoring
   * Łatwa migracja do self-hosted w przyszłości
   * Doskonałe performance benchmarks

**Alternatywa**: ChromaDB dla bardzo małych projektów (<1000 artykułów)

4. Architektura Bazy Wektorowej - Decyzja końcowa
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**❌ MySQL 9.0 VECTOR - NIE REKOMENDOWANE**

**Powody odrzucenia**:
   * Funkcjonalność VECTOR nadal eksperymentalna
   * Ograniczona wydajność dla >50k wektorów
   * Brak zaawansowanych funkcji (filtry, metadane)
   * Ryzyko lock-in na przestarzałą technologię

**✅ Migracja z przestarzałej MySQL**

**Plan migracji**:
   1. **Faza 1**: Qdrant Cloud dla embeddings
   2. **Faza 2**: Zachowanie istniejącej MySQL dla metadanych
   3. **Faza 3**: Ocena migracji głównej bazy do PostgreSQL

**Wymagane działania**
   * Setup Qdrant Cloud account w EU region
   * Implementacja synchronizacji metadanych MySQL a Qdrant

Decyzje Techniczne (Zespół deweloperski)
----------------------------------------

5. Strategia Integracji z Django
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Kontekst decyzji**
   Sposób integracji komponentów AI z istniejącą aplikacją Django wpływa na maintainability i development velocity.

**Opcje**

A) **Nowa Django App "knowledge"** (rekomendacja)
   * ✅ Czysta separacja kodu AI
   * ✅ Reuse istniejącej infrastruktury (auth, DB)
   * ✅ Django ORM dla metadanych
   * ⚠️ Tight coupling z główną aplikacją

B) **Mikroservice zewnętrzny**
   * ✅ Pełna niezależność technologiczna
   * ✅ Możliwość innego języka (np. Python FastAPI)
   * ❌ Dodatkowa infrastruktura (deployment, monitoring)
   * ❌ Duplikacja authentication

C) **Plugin/Extension istniejących apps**
   * ✅ Minimalne zmiany architektoniczne
   * ❌ Zanieczyszczenie istniejącego kodu
   * ❌ Trudne testowanie i rollback

**Rekomendacja**: Nowa aplikacja Django "knowledge"

**Wymagane działania**
   * Utworzenie nowej aplikacji Django: `python manage.py startapp knowledge`
   * Definicja interfejsów API między aplikacjami
   * Setup modeli: ContentSource, Article, ContentChunk
   * Konfiguracja URLconf i integracja z admin

6. Strategia Przechowywania Embeddings
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Kontekst decyzji**
   Sposób serializacji i przechowywania wektorów wpływa na wydajność i koszty storage.

**Opcje**

.. list-table:: Formaty Przechowywania
   :header-rows: 1

   * - Format
     - **Qdrant Cloud** (rekomendacja)
     - **JSON w PostgreSQL**
     - **Zewnętrzny file storage**
   * - **Rozmiar**
     - ✅ Optymalizowane
     - ❌ ~15KB per vector (JSON overhead)
     - ✅ 6KB (OpenAI 1536 × 4 bytes)
   * - **Wydajność query**
     - ✅ Dedykowane indeksy
     - ❌ Deserializacja przy każdym query
     - ❌ I/O dla każdego vector load
   * - **Backup prostota**
     - ✅ Managed backups
     - ✅ Część database backup
     - ⚠️ Osobne pliki do backup

**Rekomendacja**: Qdrant Cloud z PostgreSQL backup dla metadanych

**Wymagane działania**
   * Setup dual-database architecture
   * Implementacja sync mechanism między Django a Qdrant
   * Backup procedures dla obu systemów

7. Strategia Cachowania
~~~~~~~~~~~~~~~~~~~~~~

**Kontekst decyzji**
   Generowanie embeddings jest kosztowne obliczeniowo, ale strategia cache'owania może być odroczona w początkowej fazie.

**⚠️ Rekomendacja dla MVP: Pomiń cachowanie na początku**

**Uzasadnienie**:
   * **Prostota implementacji**: Mniej komponentów = mniej punktów awarii
   * **Niskie koszty w fazie testowej**: Przy małej liczbie użytkowników koszt OpenAI API będzie minimalny (€5-15/miesiąc)
   * **Szybsze uruchomienie**: Skupienie na core functionality
   * **Łatwe dodanie później**: Redis można dodać bez zmian w core logic

**Opcje dla przyszłej optymalizacji**

.. list-table:: Strategie Cache (do rozważenia przy sukcesie projektu)
   :header-rows: 1

   * - Poziom
     - **Redis**
     - **Database cache**
     - **File system**
   * - **Query embeddings**
     - ✅ Fast in-memory
     - ⚠️ Dodatkowe DB load
     - ❌ Slow I/O
   * - **Search results**
     - ✅ Ideal use case
     - ⚠️ DB load przy high traffic
     - ⚠️ Consistency problems
   * - **API responses**
     - ✅ Zmniejsza koszty OpenAI
     - ⚠️ DB load
     - ⚠️ Consistency problems

**Kiedy rozważyć cachowanie**:
   * **Koszty API**: Gdy OpenAI koszty > €50/miesiąc
   * **Liczba użytkowników**: >20 aktywnych użytkowników dziennie
   * **Powtarzalne queries**: Gdy >30% zapytań się powtarza
   * **Latencja**: Gdy search latency > 3 sekundy

**Implementacja w przyszłości**:
   * Setup Redis instance (lub wykorzystanie istniejącego)
   * Implementacja cache keys pattern (hash query → embedding)
   * TTL policy dla różnych typów danych (queries: 1h, results: 24h)

**Monitoring do implementacji cache**:

.. code-block:: python

   # Simple metrics to track when caching becomes beneficial
   class CacheMetrics:
       @staticmethod
       def track_duplicate_queries():
           """Track query repetition rate"""

       @staticmethod
       def track_api_costs():
           """Monitor monthly OpenAI costs"""

       @staticmethod
       def track_search_latency():
           """Monitor average search response time"""

8. Processing Pipeline - Batch vs Real-time
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Kontekst decyzji**
   Sposób przetwarzania nowych artykułów wpływa na real-time capabilities i resource usage.

**Opcje**

A) **Scheduled Batch Processing** (rekomendacja)
   * ✅ Prostota infrastruktury (cron + Django commands)
   * ✅ Przewidywalne zasoby
   * ✅ Łatwe debugging i monitoring
   * ✅ Batch API discounts (OpenAI)
   * ⚠️ Delay w dostępności nowych artykułów (1-6h)
   * ✅ Idealne gdy AI nie jest core feature

B) **Asynchronous z Celery**
   * ✅ Near real-time processing
   * ✅ Retry mechanisms
   * ✅ Job prioritization
   * ❌ Dodatkowa infrastruktura (Redis/RabbitMQ)
   * ❌ Więcej punktów awarii
   * ❌ Zespół musi opanować Celery

C) **Synchronous processing**
   * ✅ Prostota implementacji
   * ❌ Blocking UI podczas długiej operacji
   * ❌ Risk timeouts przy dużych artykułach

**Rekomendacja**: Scheduled Batch Processing

**Implementacja**:

.. code-block:: python

   # knowledge/management/commands/process_articles.py
   class Command(BaseCommand):
       def handle(self, *args, **options):
           # Process new/updated articles in batches
           new_articles = Article.objects.filter(processed=False)[:50]

           # Batch embedding generation
           texts = [article.content for article in new_articles]
           embeddings = openai_client.embeddings.create(
               model="text-embedding-3-small",
               input=texts
           )

           # Batch upload to Qdrant
           qdrant_client.upsert_batch(embeddings)

**Cron setup**:

.. code-block:: bash

   # /etc/cron.d/poradnia-ai
   # Process new articles every 2 hours
   0 */2 * * * www-data cd /app && python manage.py process_articles

   # Full reindex weekly (Sunday 2 AM)
   0 2 * * 0 www-data cd /app && python manage.py reindex_all

**Wymagane działania**
   * Implementacja Django management commands
   * Setup cron jobs na serwerze
   * Logging i monitoring batch jobs
   * Error handling i email notifications
