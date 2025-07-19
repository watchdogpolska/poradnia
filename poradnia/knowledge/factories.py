import factory
from django.utils import timezone
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyChoice, FuzzyInteger, FuzzyText

from poradnia.users.factories import UserFactory

from .models import Article, ArticleChunk, ContentSource, ProcessingLog, SearchLog


class ContentSourceFactory(DjangoModelFactory):
    name = factory.Sequence(lambda n: f"Content Source {n}")
    base_url = factory.LazyAttribute(
        lambda obj: f"https://{obj.name.lower().replace(' ', '')}.example.com"
    )
    api_endpoint = factory.LazyAttribute(
        lambda obj: f"{obj.base_url}/wp-json/wp/v2/posts"
    )
    is_active = True

    class Meta:
        model = ContentSource


class ArticleFactory(DjangoModelFactory):
    source = factory.SubFactory(ContentSourceFactory)
    external_id = factory.Sequence(lambda n: str(n))
    title = factory.Faker("sentence", nb_words=6)
    content = factory.Faker("text", max_nb_chars=2000)
    excerpt = factory.Faker("text", max_nb_chars=200)
    url = factory.Faker("url")
    published_at = factory.Faker("date_time_this_year", tzinfo=timezone.utc)
    modified_at = factory.LazyAttribute(lambda obj: obj.published_at)
    categories = factory.LazyFunction(lambda: ["Category 1", "Category 2"])
    tags = factory.LazyFunction(lambda: ["tag1", "tag2", "tag3"])

    class Meta:
        model = Article


class ArticleChunkFactory(DjangoModelFactory):
    article = factory.SubFactory(ArticleFactory)
    chunk_index = factory.Sequence(lambda n: n)
    content = factory.Faker("text", max_nb_chars=1000)
    token_count = FuzzyInteger(100, 300)

    class Meta:
        model = ArticleChunk


class ProcessingLogFactory(DjangoModelFactory):
    task_type = FuzzyChoice(["fetch_articles", "index_articles", "generate_embeddings"])
    status = FuzzyChoice(["running", "success", "failed"])
    result_data = factory.LazyFunction(lambda: {"processed": 10, "errors": 0})
    log_message = factory.Faker("sentence")
    command_args = factory.LazyFunction(lambda: {"source_id": 1, "batch_size": 50})

    class Meta:
        model = ProcessingLog


class SearchLogFactory(DjangoModelFactory):
    user = factory.SubFactory(UserFactory)
    query = factory.Faker("sentence", nb_words=4)
    case_id = FuzzyInteger(1, 1000)
    results_count = FuzzyInteger(0, 20)
    response_time_ms = FuzzyInteger(100, 2000)

    class Meta:
        model = SearchLog
