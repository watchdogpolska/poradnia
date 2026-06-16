n8n AI Assistant — Webhook API
================================

Overview
--------

Django sends a user question to n8n via a signed POST request. n8n immediately acknowledges
with a ``request_id``, then classifies the question, searches the FOI knowledge base, and
delivers the result asynchronously back to Django via a callback.

----

Django settings
---------------

Add the following to ``settings.py`` (values loaded from environment variables):

.. code-block:: python

   # settings.py
   N8N_ARTICLES_SEARCH_WEBHOOK       = env("N8N-ARTICLES-SEARCH-WEBHOOK")
   N8N_ARTICLES_SEARCH_WEBHOOK_TOKEN = env("N8N-ARTICLES-SEARCH-WEBHOOK-TOKEN")
   N8N_ARTICLES_SEARCH_CALLBACK      = env("N8N-ARTICLES-SEARCH-CALLBACK")
   N8N_ARTICLES_SEARCH_CALLBACK_TOKEN = env("N8N-ARTICLES-SEARCH-CALLBACK-TOKEN")

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Setting (env var name)
     - Description
   * - ``N8N-ARTICLES-SEARCH-WEBHOOK``
     - Full URL of the n8n webhook endpoint (outgoing — Django calls this)
   * - ``N8N-ARTICLES-SEARCH-WEBHOOK-TOKEN``
     - Bearer token Django sends to authenticate calls to n8n
   * - ``N8N-ARTICLES-SEARCH-CALLBACK``
     - Full URL of the Django callback endpoint (incoming — n8n calls this)
   * - ``N8N-ARTICLES-SEARCH-CALLBACK-TOKEN``
     - Bearer token n8n sends to authenticate callback calls to Django

Per-environment ``.env`` values:

.. list-table::
   :header-rows: 1
   :widths: 35 22 22 21

   * - Setting
     - DEV
     - DEMO
     - PROD
   * - ``N8N-ARTICLES-SEARCH-WEBHOOK``
     - ``<provided separately>``
     - *(same)*
     - *(same)*
   * - ``N8N-ARTICLES-SEARCH-WEBHOOK-TOKEN``
     - ``<dev-token>``
     - ``<demo-token>``
     - ``<prod-token>``
   * - ``N8N-ARTICLES-SEARCH-CALLBACK``
     - ``<dev-callback-url>``
     - ``<demo-callback-url>``
     - ``<prod-callback-url>``
   * - ``N8N-ARTICLES-SEARCH-CALLBACK-TOKEN``
     - ``<dev-token>``
     - ``<demo-token>``
     - ``<prod-token>``

.. note::

   ``N8N-ARTICLES-SEARCH-WEBHOOK-TOKEN`` and ``N8N-ARTICLES-SEARCH-CALLBACK-TOKEN`` are
   independent secrets. Use different values for each environment and each direction.

----

Step 1 — Send the request
--------------------------

``POST {N8N-ARTICLES-SEARCH-WEBHOOK}``

Headers
~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Header
     - Value
   * - ``Content-Type``
     - ``application/json``
   * - ``Authorization``
     - ``Bearer {N8N-ARTICLES-SEARCH-WEBHOOK-TOKEN}``

Request body
~~~~~~~~~~~~

.. code-block:: json

   {
     "chatInput": "Czy izba lekarska jest zobowiązana do udostępnienia informacji publicznej?",
     "environment": "PROD",
     "direct_search": false
   }

.. list-table::
   :header-rows: 1
   :widths: 20 15 15 50

   * - Field
     - Type
     - Required
     - Description
   * - ``chatInput``
     - string
     - yes
     - The user's question in natural language (Polish)
   * - ``environment``
     - string
     - yes
     - Must match ``APP_MODE``: one of ``DEV``, ``DEMO``, ``PROD``
   * - ``direct_search``
     - boolean
     - no
     - Controls the processing path (see below). Defaults to ``false``.

.. important::

   The ``environment`` value must exactly match the Django ``APP_MODE`` setting (``DEV``,
   ``DEMO``, or ``PROD``). n8n uses it to route the callback to the correct URL and to
   tag the log entry. Requests with an unrecognised value are logged but the callback
   will not be delivered.

.. note::

   **``direct_search: false`` (default)** — the question passes through the FOI classifier first:

   - If the question is FOI-related, article search runs and the callback returns ``is_foi: "TAK"``.
   - If the question is out of scope, a polite redirect message is generated and the callback
     returns ``is_foi: "NIE"``. No article search is performed.

   **``direct_search: true``** — classification is skipped entirely. The question goes straight
   to article search and the callback always returns ``is_foi: "TAK"``. Use this when the
   caller has already established that the question is FOI-related.

   This flag is also recommended when ``chatInput`` contains concatenated case context
   (multiple client messages, case history, etc.) rather than a single focused question.
   Long mixed-topic input can cause the classifier to return ``NIE`` even when a FOI
   question is present. The article search stage handles large inputs well — it first
   distils the context into 2–5 focused search phrases, filtering out emotional content
   and personal data before querying the knowledge base.

----

Step 2 — Immediate acknowledgement (synchronous)
-------------------------------------------------

n8n responds **before** AI processing begins. Django must persist ``request_id`` to match
it with the incoming callback.

**HTTP 202 Accepted**

.. code-block:: json

   {
     "request_id": "abc123-1718447823456",
     "status": "accepted"
   }

.. list-table::
   :header-rows: 1
   :widths: 20 15 65

   * - Field
     - Type
     - Description
   * - ``request_id``
     - string
     - Unique identifier for this request — store it, you will receive it back in the callback
   * - ``status``
     - string
     - Always ``"accepted"``

----

Step 3 — Receive the callback (asynchronous)
---------------------------------------------

Once processing is complete, n8n POSTs to ``{N8N-ARTICLES-SEARCH-CALLBACK}``.
n8n determines the correct callback URL from the ``environment`` field sent in Step 1:

.. list-table::
   :header-rows: 1
   :widths: 15 85

   * - APP_MODE
     - Callback URL (``N8N-ARTICLES-SEARCH-CALLBACK``)
   * - ``DEV``
     - ``<dev-callback-url>``
   * - ``DEMO``
     - ``<demo-callback-url>``
   * - ``PROD``
     - ``<prod-callback-url>``

``POST {N8N-ARTICLES-SEARCH-CALLBACK}``

Headers
~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Header
     - Value
   * - ``Content-Type``
     - ``application/json``
   * - ``Authorization``
     - ``Bearer {N8N-ARTICLES-SEARCH-CALLBACK-TOKEN}``

Callback payload — FOI question (``is_foi = TAK``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: json

   {
     "request_id": "abc123-1718447823456",
     "response": "Użyteczne artykuły w sprawie:\n- [link](https://...)\n\n**Temat:** ...\n**Podsumowanie:** ...",
     "is_foi": "TAK",
     "environment": "PROD"
   }

Callback payload — out-of-scope question (``is_foi = NIE``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: json

   {
     "request_id": "abc123-1718447823456",
     "response": "Ten asystent obsługuje wyłącznie pytania dotyczące dostępu do informacji publicznej...",
     "is_foi": "NIE",
     "environment": "PROD"
   }

Callback payload — processing error
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: json

   {
     "request_id": "abc123-1718447823456",
     "error": "processing_failed",
     "environment": "PROD"
   }

Callback fields
~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 20 15 25 40

   * - Field
     - Type
     - Present when
     - Description
   * - ``request_id``
     - string
     - always
     - Same ID returned in Step 2 — use this to match the original request
   * - ``response``
     - string
     - success only
     - AI-generated answer in Markdown
   * - ``is_foi``
     - string
     - success only
     - ``"TAK"`` if question was FOI-related, ``"NIE"`` if out of scope
   * - ``environment``
     - string
     - always
     - Echoes the ``APP_MODE`` value sent in the original request
   * - ``error``
     - string
     - failure only
     - ``"processing_failed"``

.. important::

   Django must respond to the callback with HTTP 200–299. n8n logs the returned status
   code in the ``FOI Webhook Logs`` table (``django_callback_status`` column).

----

Flow diagram
------------

.. code-block:: text

   Django                                    n8n
     |                                        |
     |-- POST {N8N-ARTICLES-SEARCH-WEBHOOK} ->|
     |   Authorization: Bearer {WEBHOOK-TOKEN}|
     |                                        | 1. Register request (Data Table)
     |<-- 202 { request_id } ---------------- | 2. Respond immediately
     |                                        | 3a. [direct_search=false] Classify question
     |                                        |     → if out-of-scope: generate OOS response
     |                                        |     → if FOI: search knowledge base
     |                                        | 3b. [direct_search=true]  Skip classification
     |                                        |     → search knowledge base directly
     |                                        | 4. Update log with response
     |<-- POST {N8N-ARTICLES-SEARCH-CALLBACK} | 5. Callback with result
     |   Authorization: Bearer {CALLBACK-TOKEN}
     |-- 200 OK -----------------------------> |

----

Recommended Django implementation
-----------------------------------

Model
~~~~~

.. code-block:: python

   class N8nArticlesSearchRequest(models.Model):
       request_id     = models.CharField(max_length=100, unique=True)
       environment    = models.CharField(max_length=10)              # DEV / DEMO / PROD
       question       = models.TextField()
       direct_search  = models.BooleanField(default=False)
       response       = models.TextField(blank=True)
       is_foi         = models.CharField(max_length=3, blank=True)   # TAK / NIE
       status         = models.CharField(max_length=20, default="pending")  # pending / completed / failed
       created_at     = models.DateTimeField(auto_now_add=True)
       updated_at     = models.DateTimeField(auto_now=True)

Sending a request
~~~~~~~~~~~~~~~~~

.. code-block:: python

   import requests
   from django.conf import settings

   def n8n_articles_search(question: str, direct_search: bool = False) -> str:
       """Send question to n8n, return request_id."""
       response = requests.post(
           settings.N8N_ARTICLES_SEARCH_WEBHOOK,
           headers={
               "Authorization": f"Bearer {settings.N8N_ARTICLES_SEARCH_WEBHOOK_TOKEN}",
               "Content-Type": "application/json",
           },
           json={
               "chatInput": question,
               "environment": settings.APP_MODE,    # DEV / DEMO / PROD
               "direct_search": direct_search,
           },
           timeout=10,
       )
       response.raise_for_status()
       data = response.json()

       N8nArticlesSearchRequest.objects.create(
           request_id=data["request_id"],
           environment=settings.APP_MODE,
           question=question,
           direct_search=direct_search,
       )
       return data["request_id"]

Receiving the callback
~~~~~~~~~~~~~~~~~~~~~~

Verify the incoming ``Authorization`` header against ``N8N-ARTICLES-SEARCH-CALLBACK-TOKEN``
before processing the payload.

.. code-block:: python

   from django.conf import settings
   from rest_framework.authentication import get_authorization_header

   class N8nArticlesSearchCallbackView(APIView):
       authentication_classes = []
       permission_classes = []

       def post(self, request):
           # Verify callback token
           auth = get_authorization_header(request).decode()
           expected = f"Bearer {settings.N8N_ARTICLES_SEARCH_CALLBACK_TOKEN}"
           if auth != expected:
               return Response({"error": "unauthorized"}, status=401)

           request_id = request.data.get("request_id")
           error = request.data.get("error")

           try:
               log = N8nArticlesSearchRequest.objects.get(request_id=request_id)
           except N8nArticlesSearchRequest.DoesNotExist:
               return Response({"error": "not_found"}, status=404)

           if error:
               log.status = "failed"
           else:
               log.response = request.data.get("response", "")
               log.is_foi = request.data.get("is_foi", "")
               log.status = "completed"

           log.save()
           return Response({"ok": True}, status=200)

----

Filtering logs by environment
------------------------------

All requests are logged in the n8n **FOI Webhook Logs** Data Table with an ``environment``
column (values: ``DEV``, ``DEMO``, ``PROD``). You can filter executions per environment
directly inside n8n without querying Django.

.. list-table::
   :header-rows: 1
   :widths: 30 15 55

   * - Column
     - Type
     - Description
   * - ``request_id``
     - string
     - Unique request identifier
   * - ``environment``
     - string
     - ``DEV`` / ``DEMO`` / ``PROD``
   * - ``received_at``
     - string
     - ISO 8601 timestamp when request arrived
   * - ``request_body``
     - string
     - Full JSON body of the original request
   * - ``response_text``
     - string
     - AI-generated response
   * - ``is_foi``
     - string
     - ``TAK`` / ``NIE``
   * - ``processed_at``
     - string
     - ISO 8601 timestamp when processing completed
   * - ``django_callback_status``
     - number
     - HTTP status code returned by Django callback
