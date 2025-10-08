Architektura Systemu AI
=======================

Przegląd Architektury
---------------------

System AI dla Poradni Prawnej został zaprojektowany jako rozszerzona architektura istniejącej aplikacji Django, z naciskiem na modularność, skalowalność i zgodność z RODO. Architektura wspiera rozwój iteracyjny - od prostej wyszukiwarki artykułów do zaawansowanego systemu RAG.

**Kluczowe założenia architektoniczne**:
   * AI może być wyłączony (feature flags)
   * Usługi SaaS dla embeddings i bazy wektorowej
   * Przetwarzanie wsadowe zamiast czasu rzeczywistego
   * Architektura dwubazowa: MySQL dla metadanych + Qdrant Cloud dla embeddings

Architektura Wysokiego Poziomu
------------------------------

.. code-block:: text

   ┌─────────────────────────────────────────────────────────────────┐
   │                   WARSTWA FRONTENDOWA                           │
   ├─────────────────────────────────────────────────────────────────┤
   │  Interfejs Django Admin     │  Punkty końcowe REST API          │
   │  ┌─────────────────────┐    │  ┌─────────────────────────────┐   │
   │  │ Widget Wiedzy       │    │  │ /api/knowledge/search/      │   │
   │  │ Rozszerzenia Spraw  │    │  │ /api/knowledge/suggest/     │   │
   │  │ Panel Wyszukiwania  │    │  │ /api/knowledge/health/      │   │
   │  └─────────────────────┘    │  └─────────────────────────────┘   │
   └─────────────────────────────────────────────────────────────────┘
                                    │
   ┌─────────────────────────────────────────────────────────────────┐
   │                  WARSTWA APLIKACYJNA                            │
   ├─────────────────────────────────────────────────────────────────┤
   │  Aplikacja Django Knowledge                                     │
   │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
   │  │ Serwis          │  │ Serwis          │  │ Procesor        │ │
   │  │ Wyszukiwania    │  │ Embeddings      │  │ Tekstu          │ │
   │  │ • Proc. zapytań │  │ • OpenAI API    │  │ • Czyszczenie   │ │
   │  │ • Wyszuk. wekt. │  │ • Cache zapytań │  │ • Fragmentacja  │ │
   │  │ • Ranking wynik.│  │ • Proc. wsadowe │  │ • Sanityzacja   │ │
   │  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
   └─────────────────────────────────────────────────────────────────┘
                                    │
   ┌─────────────────────────────────────────────────────────────────┐
   │                    WARSTWA DANYCH                               │
   ├─────────────────────────────────────────────────────────────────┤
   │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
   │  │ Qdrant Cloud    │  │ MySQL           │  │ Redis Cache     │  │
   │  │ (Baza Wektorów) │  │ (Metadane)      │  │                 │  │
   │  │ • Embeddings    │  │ • Meta artykułów│  │ • Cache zapytań │  │
   │  │ • Podobieństwo  │  │ • Dane użytk.   │  │ • Cache wyników │  │
   │  │ • Region UE     │  │ • Logi audytu   │  │ • Sesje         │  │
   │  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
   └─────────────────────────────────────────────────────────────────┘
                                    │
   ┌─────────────────────────────────────────────────────────────────┐
   │                 WARSTWA POZYSKIWANIA                            │
   ├─────────────────────────────────────────────────────────────────┤
   │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
   │  │ Crawler Treści  │  │ Procesor        │  │ Zewnętrzne API  │ │
   │  │                 │  │ Wsadowy         │  │                 │ │
   │  │ • WordPress API │  │ • Zadania cron  │  │ • OpenAI API    │ │
   │  │ • Procesor PDF  │  │ • Polecenia mgmt│  │ • WordPress     │ │
   │  │ • Harmonogram   │  │ • Obsługa błędów│  │ • Usługi OCR    │ │
   │  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
   └─────────────────────────────────────────────────────────────────┘

Alternatywna Architektura Azure-Native
--------------------------------------

**Kontekst**
   Alternatywne podejście wykorzystujące w pełni zarządzane usługi Azure dla zespołów preferujących mniejszą ilość własnego kodu do zarządzania.

**Architektura Azure-Native - Wysokiego Poziomu**

.. code-block:: text

   ┌─────────────────────────────────────────────────────────────────┐
   │                   WARSTWA FRONTENDOWA                           │
   ├─────────────────────────────────────────────────────────────────┤
   │  Interfejs Django Admin     │  Punkty końcowe REST API          │
   │  ┌─────────────────────┐    │  ┌─────────────────────────────┐   │
   │  │ Widget Wiedzy       │    │  │ /api/knowledge/search/      │   │
   │  │ Azure Search Query  │    │  │ /api/knowledge/rag/         │   │
   │  │ RAG Responses       │    │  │ /api/knowledge/health/      │   │
   │  └─────────────────────┘    │  └─────────────────────────────┘   │
   └─────────────────────────────────────────────────────────────────┘
                                    │
   ┌─────────────────────────────────────────────────────────────────┐
   │                  WARSTWA APLIKACYJNA                            │
   ├─────────────────────────────────────────────────────────────────┤
   │  Aplikacja Django Knowledge                                     │
   │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
   │  │ Azure Search    │  │ Azure OpenAI    │  │ Content         │ │
   │  │ Service Client  │  │ "On Your Data"  │  │ Sync Service    │ │
   │  │ • Query proxy   │  │ • RAG endpoint  │  │ • WP → Blob     │ │
   │  │ • Filter logic  │  │ • Citation      │  │ • Status track  │ │
   │  │ • Result format │  │ • Response gen. │  │ • Error handle  │ │
   │  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
   └─────────────────────────────────────────────────────────────────┘
                                    │
   ┌─────────────────────────────────────────────────────────────────┐
   │                  WARSTWA AZURE USŁUG                           │
   ├─────────────────────────────────────────────────────────────────┤
   │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
   │  │ Azure AI Search │  │ Azure Blob      │  │ Document        │  │
   │  │ Index           │  │ Storage         │  │ Intelligence    │  │
   │  │ • Vector store  │  │ • Raw content   │  │ • PDF OCR       │  │
   │  │ • Full text     │  │ • WP exports    │  │ • Layout parse  │  │
   │  │ • Metadata      │  │ • Attachments   │  │ • Table extract │  │
   │  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
   └─────────────────────────────────────────────────────────────────┘
                                    │
   ┌─────────────────────────────────────────────────────────────────┐
   │                WARSTWA AUTOMATYCZNEJ INGESTION                 │
   ├─────────────────────────────────────────────────────────────────┤
   │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
   │  │ Azure AI Search │  │ Azure OpenAI    │  │ MySQL (legacy)  │ │
   │  │ Indexer         │  │ Embedding Skill │  │ Metadane        │ │
   │  │ • Auto schedule │  │ • Integrated    │  │ • Content refs  │ │
   │  │ • Data source   │  │ • Batch embed   │  │ • User data     │ │
   │  │ • Error retry   │  │ • Auto chunk    │  │ • Audit logs    │ │
   │  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
   └─────────────────────────────────────────────────────────────────┘

**Przepływ Danych Azure-Native**

.. code-block:: text

   1. Content Ingestion:
   WordPress API → [PullScript] → Azure Blob Storage
                                        ↓
   2. Auto Processing:
   Azure AI Search Indexer (scheduled) → Document Intelligence (PDF)
                                        ↓
   3. Vectorization:
   Azure OpenAI Embedding Skill → chunks → Azure AI Search Index
                                        ↓
   4. Search & RAG:
   Django Query → Azure AI Search → Azure OpenAI "On Your Data" → Response

**Komponenty Azure-Native**

**Azure AI Search Index**
   Centralne repozytorium dla wektorów i metadanych

.. code-block:: python

   # Definicja indeksu Azure AI Search
   index_definition = {
       "name": "knowledge-base",
       "fields": [
           {"name": "id", "type": "Edm.String", "key": True},
           {"name": "content", "type": "Edm.String", "searchable": True},
           {"name": "title", "type": "Edm.String", "searchable": True, "filterable": True},
           {"name": "url", "type": "Edm.String", "filterable": True},
           {"name": "source", "type": "Edm.String", "filterable": True},
           {"name": "published_date", "type": "Edm.DateTimeOffset", "filterable": True, "sortable": True},
           {"name": "category", "type": "Edm.String", "filterable": True},
           {"name": "content_vector", "type": "Collection(Edm.Single)",
            "vectorSearchDimensions": 1536, "vectorSearchProfileName": "default"},
       ],
       "vectorSearch": {
           "algorithms": [
               {"name": "hnsw-cosine", "kind": "hnsw", "hnswParameters": {"m": 4, "efConstruction": 400}}
           ],
           "profiles": [
               {"name": "default", "algorithm": "hnsw-cosine"}
           ]
       }
   }

**Azure AI Search Service Client**
   Serwis Django dla komunikacji z Azure AI Search

.. code-block:: python

   from azure.search.documents import SearchClient
   from azure.search.documents.models import VectorizedQuery

   class AzureSearchService:
       def __init__(self):
           self.search_client = SearchClient(
               endpoint=settings.AZURE_SEARCH_ENDPOINT,
               index_name="knowledge-base",
               credential=DefaultAzureCredential()
           )
           self.openai_client = AzureOpenAI(
               api_version="2024-02-01",
               azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
               azure_ad_token_provider=get_bearer_token_provider(
                   DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
               )
           )

       def search_articles(self, query: str, filters: dict = None, limit: int = 10) -> List[dict]:
           """
           Hybrydowe wyszukiwanie: wektory + full text + filtry
           """
           # Generowanie embedding dla zapytania
           embedding_response = self.openai_client.embeddings.create(
               model="text-embedding-3-small",
               input=query
           )
           query_vector = embedding_response.data[0].embedding

           # Przygotowanie zapytania wektorowego
           vector_query = VectorizedQuery(
               vector=query_vector,
               k_nearest_neighbors=50,
               fields="content_vector"
           )

           # Budowanie filtrów
           filter_expression = self._build_filter_expression(filters) if filters else None

           # Wykonanie hybrydowego search
           results = self.search_client.search(
               search_text=query,
               vector_queries=[vector_query],
               filter=filter_expression,
               top=limit,
               include_total_count=True
           )

           return [
               {
                   "id": result["id"],
                   "title": result["title"],
                   "content": result["content"][:500],
                   "url": result["url"],
                   "score": result["@search.score"],
                   "source": result["source"],
                   "published_date": result["published_date"]
               }
               for result in results
           ]

       def generate_rag_response(self, question: str) -> dict:
           """
           Wykorzystanie Azure OpenAI "On Your Data" dla RAG
           """
           response = self.openai_client.chat.completions.create(
               model="gpt-4o",
               messages=[
                   {"role": "system", "content": "Jesteś ekspertem prawnym specjalizującym się w dostępie do informacji publicznej. Odpowiadaj na podstawie dostarczonych dokumentów."},
                   {"role": "user", "content": question}
               ],
               extra_body={
                   "data_sources": [{
                       "type": "azure_search",
                       "parameters": {
                           "endpoint": settings.AZURE_SEARCH_ENDPOINT,
                           "index_name": "knowledge-base",
                           "authentication": {
                               "type": "api_key",
                               "key": settings.AZURE_SEARCH_API_KEY
                           },
                           "top_n_documents": 5,
                           "in_scope": True,
                           "role_information": "Jesteś prawnikiem specjalizującym się w dostępie do informacji publicznej."
                       }
                   }]
               }
           )

           return {
               "response": response.choices[0].message.content,
               "citations": self._extract_citations(response.choices[0].message),
               "usage": response.usage
           }

**Azure Indexer Configuration**
   Automatyczny indexer dla bez-kodowej ingestion

.. code-block:: python

   from azure.search.documents.indexes import SearchIndexerClient

   class AzureIndexerService:
       def setup_automated_indexing(self):
           """
           Konfiguracja automatycznego indeksowania z Azure Blob
           """
           indexer_client = SearchIndexerClient(
               endpoint=settings.AZURE_SEARCH_ENDPOINT,
               credential=DefaultAzureCredential()
           )

           # Data Source - Azure Blob Storage
           data_source = {
               "name": "wordpress-content",
               "type": "azureblob",
               "connectionString": settings.AZURE_BLOB_CONNECTION_STRING,
               "container": {"name": "wordpress-exports"}
           }

           # Skillset z Azure OpenAI Embedding
           skillset = {
               "name": "content-processing",
               "skills": [
                   {
                       "@odata.type": "#Microsoft.Skills.Text.SplitSkill",
                       "textSplitMode": "pages",
                       "maximumPageLength": 2000,
                       "inputs": [{"name": "text", "source": "/document/content"}],
                       "outputs": [{"name": "textItems", "targetName": "chunks"}]
                   },
                   {
                       "@odata.type": "#Microsoft.Skills.Text.AzureOpenAIEmbeddingSkill",
                       "resourceUri": settings.AZURE_OPENAI_ENDPOINT,
                       "deploymentId": "text-embedding-3-small",
                       "inputs": [{"name": "text", "source": "/document/chunks/*"}],
                       "outputs": [{"name": "embedding", "targetName": "vector"}]
                   }
               ]
           }

           # Indexer - łączy data source, skillset i target index
           indexer = {
               "name": "wordpress-indexer",
               "dataSourceName": "wordpress-content",
               "skillsetName": "content-processing",
               "targetIndexName": "knowledge-base",
               "schedule": {"interval": "PT6H"},  # Co 6 godzin
               "fieldMappings": [
                   {"sourceFieldName": "metadata_storage_name", "targetFieldName": "title"},
                   {"sourceFieldName": "metadata_storage_path", "targetFieldName": "url"},
                   {"sourceFieldName": "content", "targetFieldName": "content"}
               ],
               "outputFieldMappings": [
                   {"sourceFieldName": "/document/chunks/*/vector", "targetFieldName": "content_vector"}
               ]
           }

           # Utworzenie komponentów
           indexer_client.create_data_source(data_source)
           indexer_client.create_skillset(skillset)
           indexer_client.create_indexer(indexer)

**Content Sync Service**
   Synchronizacja między WordPress a Azure Blob

.. code-block:: python

   from azure.storage.blob import BlobServiceClient
   import requests

   class AzureContentSyncService:
       def __init__(self):
           self.blob_service = BlobServiceClient(
               account_url=settings.AZURE_BLOB_ACCOUNT_URL,
               credential=DefaultAzureCredential()
           )
           self.container_name = "wordpress-exports"

       def sync_wordpress_content(self, since_hours: int = 6):
           """
           Synchronizacja treści z WordPress do Azure Blob
           """
           # Pobranie zaktualizowanych artykułów z WordPress
           since_timestamp = (datetime.now() - timedelta(hours=since_hours)).isoformat()
           wp_response = requests.get(
               f"{settings.WORDPRESS_API_URL}/wp/v2/posts",
               params={"modified_after": since_timestamp, "per_page": 100}
           )

           articles = wp_response.json()

           for article in articles:
               # Przygotowanie metadanych
               blob_name = f"articles/{article['id']}.json"
               metadata = {
                   "title": article['title']['rendered'],
                   "published_date": article['date'],
                   "modified_date": article['modified'],
                   "source": "wordpress",
                   "category": self._extract_category(article),
                   "url": article['link']
               }

               # Upload artykułu jako JSON blob
               blob_data = {
                   "content": self._clean_html(article['content']['rendered']),
                   "metadata": metadata
               }

               blob_client = self.blob_service.get_blob_client(
                   container=self.container_name,
                   blob=blob_name
               )

               blob_client.upload_blob(
                   json.dumps(blob_data, ensure_ascii=False).encode('utf-8'),
                   metadata=metadata,
                   overwrite=True
               )

               # Aktualizacja statusu w MySQL
               Article.objects.update_or_create(
                   external_id=str(article['id']),
                   defaults={
                       'title': article['title']['rendered'],
                       'url': article['link'],
                       'content': blob_data['content'],
                       'published_date': article['date'],
                       'modified_date': article['modified'],
                       'azure_blob_path': blob_name,
                       'sync_status': 'uploaded'
                   }
               )

**Porównanie Architektur**

.. list-table:: Rekomendowana vs Azure-Native
   :header-rows: 1

   * - Aspekt
     - **Rekomendowana (Qdrant + OpenAI)**
     - **Azure-Native**
   * - **Konfiguracja**
     - Więcej kodu Python
     - Więcej konfiguracji Azure portal
   * - **Vendor lock-in**
     - ✅ Niski (open source Qdrant)
     - ⚠️ Średni (Azure AI Search)
   * - **Maintenance**
     - ⚠️ Zarządzanie pipeline'em
     - ✅ Fully managed indexing
   * - **Koszty miesięczne**
     - €50-70 (Qdrant + OpenAI)
     - €80-120 (Azure AI Search + OpenAI)
   * - **PDF Processing**
     - ⚠️ Basic (PyPDF2/pdfplumber)
     - ✅ Advanced (Document Intelligence)
   * - **RAG out-of-box**
     - ❌ Custom implementation
     - ✅ "On Your Data" ready
   * - **Learning curve**
     - ✅ Python-focused
     - ⚠️ Azure ecosystem knowledge
   * - **Debugowanie**
     - ✅ Full code control
     - ⚠️ Black box indexer
   * - **Skalowanie**
     - ⚠️ Manual (resize Qdrant)
     - ✅ Auto (Azure AI Search)

**⚠️ Uwaga**: Obecna rekomendacja (Qdrant Cloud + OpenAI API) pozostaje **preferowanym wyborem** dla zespołów z ograniczonymi zasobami i małym doświadczeniem z Azure. Azure-native approach jest alternatywą do rozważenia przy większym doświadczeniu z Azure lub wymaganiach zaawansowanego PDF processing.

Komponenty Systemu
------------------

Warstwa Frontendowa
~~~~~~~~~~~~~~~~~~

**Interfejs Django Admin**
   Rozszerzone interfejsy administratora Django z widgetami wyszukiwania AI

   * **Widget Wiedzy** - widget wyszukiwania zintegrowany z formularzami spraw
   * **Panel Wyszukiwania** - dedykowana strona wyszukiwania z zaawansowanymi filtrami
   * **Rozszerzenia Spraw** - rozszerzenia formularzy Cases z sugerowanymi artykułami

**Punkty Końcowe REST API**
   RESTful API dla aplikacji zewnętrznych i integracji

   * ``GET /api/knowledge/search/?q=<zapytanie>`` - wyszukiwanie semantyczne
   * ``GET /api/knowledge/suggest/?case_id=<id>`` - sugestie dla konkretnej sprawy
   * ``GET /api/knowledge/health/`` - sprawdzenie zdrowia dla monitorowania

Warstwa Aplikacyjna
~~~~~~~~~~~~~~~~~~~

**Serwis Wyszukiwania**
   Główny serwis obsługujący wyszukiwanie semantyczne

.. code-block:: python

   class SearchService:
       def search_articles(self, query: str, filters: dict = None) -> List[SearchResult]:
           """
           Główna metoda wyszukiwania semantycznego

           Args:
               query: Zapytanie w języku naturalnym
               filters: Opcjonalne filtry (data, kategoria, źródło)

           Returns:
               Lista wyników posortowana według wyniku relevance
           """

       def suggest_for_case(self, case_id: int) -> List[SearchResult]:
           """
           Sugerowanie artykułów na podstawie treści sprawy
           """

       def get_similar_cases(self, case_id: int) -> List[CaseResult]:
           """
           Wyszukiwanie podobnych spraw (Etap 2)
           """

**Serwis Embeddings**
   Serwis do zarządzania embeddings z wykorzystaniem OpenAI API

.. code-block:: python

   class EmbeddingService:
       def __init__(self):
           """
           Inicjalizacja klienta OpenAI
           """
           self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
           self.cache = cache  # Cache Redis

       def generate_embedding(self, text: str) -> np.ndarray:
           """
           Generowanie embedding dla pojedynczego tekstu z cache
           """
           cache_key = f"emb:query:{hashlib.md5(text.encode()).hexdigest()}"
           cached = self.cache.get(cache_key)
           if cached:
               return np.frombuffer(cached, dtype=np.float32)

           response = self.client.embeddings.create(
               model="text-embedding-3-small",
               input=text
           )
           embedding = np.array(response.data[0].embedding, dtype=np.float32)

           # Cache na 1 godzinę
           self.cache.set(cache_key, embedding.tobytes(), timeout=3600)
           return embedding

       def batch_generate(self, texts: List[str]) -> List[np.ndarray]:
           """
           Generowanie embeddings w trybie wsadowym dla wydajności i kosztów
           """
           response = self.client.embeddings.create(
               model="text-embedding-3-small",
               input=texts
           )
           return [np.array(data.embedding, dtype=np.float32) for data in response.data]

**Procesor Tekstu**
   Serwis do przetwarzania i czyszczenia tekstu

.. code-block:: python

   class TextProcessor:
       def clean_html(self, html_content: str) -> str:
           """Usuwanie tagów HTML i czyszczenie tekstu"""

       def chunk_text(self, text: str, chunk_size: int = 500) -> List[TextChunk]:
           """Podział tekstu na semantyczne fragmenty"""

       def anonymize_personal_data(self, text: str) -> str:
           """Anonimizacja danych osobowych (RODO)"""

Warstwa Danych
~~~~~~~~~~~~~~

**Qdrant Cloud**
   Zarządzana baza wektorowa dla embeddings

.. code-block:: python

   # Konfiguracja kolekcji Qdrant
   from qdrant_client import QdrantClient
   from qdrant_client.models import VectorParams, Distance

   client = QdrantClient(
       url=settings.QDRANT_URL,
       api_key=settings.QDRANT_API_KEY,
       prefer_grpc=True
   )

   # Konfiguracja kolekcji
   collection_config = {
       "vectors": VectorParams(
           size=1536,  # OpenAI text-embedding-3-small
           distance=Distance.COSINE
       ),
       "payload_schema": {
           "article_id": "integer",
           "title": "text",
           "url": "text",
           "content_preview": "text",
           "chunk_index": "integer",
           "published_date": "datetime",
           "source": "text",
           "category": "text"
       }
   }

**MySQL**
   Główna baza danych aplikacji zawierająca metadane (zachowana z systemu legacy)

.. code-block:: python

   # Modele Django
   class ContentSource(models.Model):
       name = models.CharField(max_length=100)
       base_url = models.URLField()
       api_endpoint = models.URLField(null=True, blank=True)
       is_active = models.BooleanField(default=True)
       crawl_frequency_hours = models.IntegerField(default=6)
       progress_cursor = models.JSONField(default=dict)

   class Article(models.Model):
       source = models.ForeignKey(ContentSource, on_delete=models.CASCADE)
       external_id = models.CharField(max_length=100)
       title = models.CharField(max_length=500)
       url = models.URLField()
       content = models.TextField()
       published_date = models.DateTimeField()
       modified_date = models.DateTimeField()
       tags = models.JSONField(default=list)
       category = models.CharField(max_length=100, null=True)
       language = models.CharField(max_length=10, default='pl')

       # Status przetwarzania AI
       processed = models.BooleanField(default=False)
       processed_at = models.DateTimeField(null=True, blank=True)
       embedding_model = models.CharField(max_length=100, default='text-embedding-3-small')

   class ContentChunk(models.Model):
       """Metadane dla fragmentów przechowywanych w bazie embeddings"""
       article = models.ForeignKey(Article, on_delete=models.CASCADE)
       chunk_index = models.IntegerField()
       content_preview = models.CharField(max_length=200)  # Pierwsze 200 znaków
       token_count = models.IntegerField()
       qdrant_point_id = models.CharField(max_length=100, unique=True)
       created_at = models.DateTimeField(auto_now_add=True)

**Cache Redis**
   Cache dla embeddings zapytań i wyników wyszukiwania

.. code-block:: python

   # Strategia cache
   cache_patterns = {
       "query_embedding": "emb:query:{query_hash}",  # TTL: 1 godzina
       "search_results": "search:{query_hash}:{filters_hash}",  # TTL: 24 godziny
       "article_popularity": "popularity:{article_id}",  # TTL: 7 dni
       "api_costs": "costs:openai:{month}",  # Śledzenie kosztów API
   }

Warstwa Pozyskiwania
~~~~~~~~~~~~~~~~~~~

**Crawler Treści**
   System pobierania treści z źródeł zewnętrznych

.. code-block:: python

   class WordPressCrawler:
       def crawl_updates(self, since_hours: int = 6) -> Iterator[ArticleData]:
           """
           Pobieranie zaktualizowanych artykułów z WordPress API
           """

   class PDFProcessor:
       def extract_text(self, pdf_path: str) -> str:
           """
           Ekstrakcja tekstu z plików PDF z fallbackiem OCR
           """

**Batch Processor**
   Polecenia zarządzania Django dla przetwarzania wsadowego

.. code-block:: python

   # knowledge/management/commands/process_articles.py
   class Command(BaseCommand):
       help = 'Przetwarzanie nowych artykułów i generowanie embeddings'

       def handle(self, *args, **options):
           embedding_service = EmbeddingService()
           text_processor = TextProcessor()
           qdrant_service = QdrantService()

           # Pobranie nieprzetworzonych artykułów
           articles = Article.objects.filter(processed=False)[:50]

           for article in articles:
               try:
                   # Czyszczenie i fragmentacja tekstu
                   clean_text = text_processor.clean_html(article.content)
                   chunks = text_processor.chunk_text(clean_text)

                   # Generowanie embeddings w trybie wsadowym
                   texts = [chunk.content for chunk in chunks]
                   embeddings = embedding_service.batch_generate(texts)

                   # Przechowywanie w Qdrant
                   for chunk, embedding in zip(chunks, embeddings):
                       point_id = qdrant_service.upsert_chunk(
                           article_id=article.id,
                           chunk_index=chunk.index,
                           content=chunk.content,
                           embedding=embedding,
                           metadata={
                               'title': article.title,
                               'url': article.url,
                               'published_date': article.published_date,
                               'category': article.category
                           }
                       )

                       # Przechowywanie metadanych w MySQL
                       ContentChunk.objects.create(
                           article=article,
                           chunk_index=chunk.index,
                           content_preview=chunk.content[:200],
                           token_count=chunk.token_count,
                           qdrant_point_id=point_id
                       )

                   # Oznaczenie jako przetworzone
                   article.processed = True
                   article.processed_at = timezone.now()
                   article.save()

                   self.stdout.write(
                       self.style.SUCCESS(f'Przetworzono artykuł {article.id}')
                   )

               except Exception as e:
                   self.stdout.write(
                       self.style.ERROR(f'Błąd przetwarzania artykułu {article.id}: {e}')
                   )

**Django Admin dla ProcessingLog**
   Interfejs administracyjny do monitorowania zadań batch processing

Integracja z Zewnętrznymi API
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Integracja OpenAI API**

**Integracja Qdrant Cloud**

.. code-block:: python

   class QdrantService:
       def __init__(self):
           self.client = QdrantClient(
               url=settings.QDRANT_URL,
               api_key=settings.QDRANT_API_KEY,
               prefer_grpc=True
           )

       def upsert_chunk(self, article_id: int, chunk_index: int,
                       content: str, embedding: np.ndarray, metadata: dict) -> str:
           """
           Wstawienie lub aktualizacja fragmentu w Qdrant
           """
           point_id = f"{article_id}_{chunk_index}"

           payload = {
               "article_id": article_id,
               "chunk_index": chunk_index,
               "content_preview": content[:200],
               **metadata
           }

           self.client.upsert(
               collection_name="knowledge_base",
               points=[{
                   "id": point_id,
                   "vector": embedding.tolist(),
                   "payload": payload
               }]
           )

           return point_id

       def search_similar(self, query_embedding: np.ndarray,
                         limit: int = 10, filters: dict = None) -> List[dict]:
           """
           Wyszukiwanie podobnych fragmentów
           """
           search_filter = None
           if filters:
               search_filter = self._build_filter(filters)

           results = self.client.search(
               collection_name="knowledge_base",
               query_vector=query_embedding.tolist(),
               limit=limit,
               query_filter=search_filter
           )

           return [
               {
                   "article_id": hit.payload["article_id"],
                   "chunk_index": hit.payload["chunk_index"],
                   "score": hit.score,
                   "content_preview": hit.payload["content_preview"],
                   "metadata": hit.payload
               }
               for hit in results
           ]

**Serwis Embeddings**
   Centralizowany serwis do zarządzania wszystkimi operacjami embeddings

.. code-block:: python

   class EmbeddingService:
       def __init__(self):
           self.openai_service = OpenAIService()
           self.cache = cache

       def get_query_embedding(self, query: str) -> np.ndarray:
           """
           Pobranie embedding dla zapytania z cache
           """
           cache_key = f"emb:query:{hashlib.md5(query.encode()).hexdigest()}"
           cached = self.cache.get(cache_key)

           if cached:
               return np.frombuffer(cached, dtype=np.float32)

           # Sprawdzenie budżetu przed wywołaniem API
           self.openai_service.check_budget()

           embedding = self.openai_service.generate_embedding(query)

           # Cache na 1 godzinę
           self.cache.set(cache_key, embedding.tobytes(), timeout=3600)

           return embedding

       def batch_process_articles(self, articles: List[Article]) -> None:
           """
           Przetwarzanie wsadowe artykułów
           """
           for batch in self._batch_iterator(articles, batch_size=10):
               texts = []
               metadata = []

               for article in batch:
                   chunks = self._chunk_article(article)
                   for chunk in chunks:
                       texts.append(chunk.content)
                       metadata.append({
                           'article': article,
                           'chunk_index': chunk.index,
                           'chunk': chunk
                       })

               # Generowanie embeddings w trybie wsadowym
               embeddings = self.openai_service.batch_generate(texts)

               # Przechowywanie w Qdrant
               for embedding, meta in zip(embeddings, metadata):
                   self._store_embedding(
                       embedding=embedding,
                       article=meta['article'],
                       chunk=meta['chunk']
                   )

Architektura Bezpieczeństwa
~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Zgodność z RODO**

.. code-block:: python

   # gdpr.py
   class GDPRCompliantAIService:
       def process_user_query(self, query: str, user: User):
           # Sprawdzenie zgody użytkownika na przetwarzanie AI
           # if not user.profile.ai_processing_consent:
           #  raise AIProcessingNotConsentedException()

           # Anonimizacja zapytania przed wysłaniem do OpenAI
           anonymized_query = self.anonymize_personal_data(query)

           # Logowanie dla ścieżki audytu
           SearchAuditLog.objects.create(
               user=user,
               original_query_hash=hashlib.sha256(query.encode()).hexdigest(),
               anonymized_query=anonymized_query,
               timestamp=timezone.now()
           )

           return self.search_with_ai(anonymized_query)

       def anonymize_personal_data(self, text: str) -> str:
           """Usuwanie/maskowanie danych osobowych przed wywołaniami API"""
           # Usuwanie emaili, numerów telefonów, nazwisk itp.
           patterns = {
               'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
               'phone': r'\b\d{3}[-.]?\d{3}[-.]?\d{3}\b',
               'pesel': r'\b\d{11}\b',
               'nip': r'\b\d{3}-\d{3}-\d{2}-\d{2}\b'
           }

           anonymized_text = text
           for pattern_name, pattern in patterns.items():
               anonymized_text = re.sub(pattern, f'[{pattern_name.upper()}_MASKED]', anonymized_text)

           return anonymized_text


Architektura Wdrożenia
~~~~~~~~~~~~~~~~~~~~~~

**Konfiguracja Środowiska**

.. code-block:: yaml

   # fragment docker-compose.yml
   services:
     web:
       environment:
         - ENABLE_AI_SEARCH=true
         - OPENAI_API_KEY=${OPENAI_API_KEY}
         - QDRANT_URL=${QDRANT_URL}
         - QDRANT_API_KEY=${QDRANT_API_KEY}

     redis:
       image: redis:7
       command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru

**Konfiguracja Zadań Cron**

.. code-block:: bash

   # /etc/cron.d/poradnia-ai
   # Pobieranie nowych artykułów co 2 godziny
   0 */2 * * * www-data cd /app && python manage.py fetch_articles

   # Indeksowanie nowych artykułów co 2 godziny
   15 */2 * * * www-data cd /app && python manage.py index_articles
