from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from poradnia.knowledge.factories import (
    ArticleChunkFactory,
    ArticleFactory,
    ContentSourceFactory,
    ProcessingLogFactory,
    SearchLogFactory,
)
from poradnia.knowledge.models import (
    Article,
    ArticleChunk,
    ContentSource,
    ProcessingLog,
    SearchLog,
)
from poradnia.users.factories import UserFactory


class ContentSourceModelTest(TestCase):
    def test_str_representation(self):
        source = ContentSourceFactory(name="Test Source")
        self.assertEqual(str(source), "Test Source")

    def test_active_queryset(self):
        active_source = ContentSourceFactory(is_active=True)
        inactive_source = ContentSourceFactory(is_active=False)

        active_sources = ContentSource.objects.active()
        self.assertIn(active_source, active_sources)
        self.assertNotIn(inactive_source, active_sources)

    def test_creation_timestamp(self):
        source = ContentSourceFactory()
        self.assertIsNotNone(source.created_at)
        self.assertIsNone(source.last_sync)


class ArticleModelTest(TestCase):
    def test_str_representation(self):
        article = ArticleFactory(title="Test Article")
        self.assertEqual(str(article), "Test Article")

    def test_unique_together_constraint(self):
        source = ContentSourceFactory()
        ArticleFactory(source=source, external_id="123")

        # Should not be able to create another article with same source and external_id
        with self.assertRaises(Exception):
            ArticleFactory(source=source, external_id="123")

    def test_published_queryset(self):
        published_article = ArticleFactory(published_at=timezone.now())
        unpublished_article = ArticleFactory(published_at=None)

        published_articles = Article.objects.published()
        self.assertIn(published_article, published_articles)
        self.assertNotIn(unpublished_article, published_articles)

    def test_for_source_queryset(self):
        source1 = ContentSourceFactory()
        source2 = ContentSourceFactory()
        article1 = ArticleFactory(source=source1)
        article2 = ArticleFactory(source=source2)

        articles_for_source1 = Article.objects.for_source(source1)
        self.assertIn(article1, articles_for_source1)
        self.assertNotIn(article2, articles_for_source1)

    def test_default_values(self):
        article = ArticleFactory(categories=[], tags=[])
        self.assertEqual(article.categories, [])
        self.assertEqual(article.tags, [])
        self.assertIsNotNone(article.created_at)
        self.assertIsNotNone(article.updated_at)


class ArticleChunkModelTest(TestCase):
    def test_str_representation(self):
        article = ArticleFactory(title="Test Article")
        chunk = ArticleChunkFactory(article=article, chunk_index=1)
        self.assertEqual(str(chunk), "Test Article - Chunk 1")

    def test_unique_together_constraint(self):
        article = ArticleFactory()
        ArticleChunkFactory(article=article, chunk_index=1)

        # Should not be able to create another chunk with same article and chunk_index
        with self.assertRaises(Exception):
            ArticleChunkFactory(article=article, chunk_index=1)

    def test_for_article_queryset(self):
        article1 = ArticleFactory()
        article2 = ArticleFactory()
        chunk1 = ArticleChunkFactory(article=article1)
        chunk2 = ArticleChunkFactory(article=article2)

        chunks_for_article1 = ArticleChunk.objects.for_article(article1)
        self.assertIn(chunk1, chunks_for_article1)
        self.assertNotIn(chunk2, chunks_for_article1)

    def test_with_embeddings_queryset(self):
        chunk_with_embedding = ArticleChunkFactory(embedding=[0.1, 0.2, 0.3])
        chunk_without_embedding = ArticleChunkFactory(embedding=None)

        chunks_with_embeddings = ArticleChunk.objects.with_embeddings()
        self.assertIn(chunk_with_embedding, chunks_with_embeddings)
        self.assertNotIn(chunk_without_embedding, chunks_with_embeddings)


class ProcessingLogModelTest(TestCase):
    def test_str_representation(self):
        log = ProcessingLogFactory(task_type="fetch_articles", status="success")
        # Check that the string representation is formed correctly
        result = str(log)
        self.assertIn("fetch_articles", result)
        self.assertIn("success", result)
        self.assertIn(" - ", result)

    def test_duration_property(self):
        started_at = timezone.now()
        finished_at = started_at + timedelta(minutes=5)

        log = ProcessingLogFactory(started_at=started_at, finished_at=finished_at)
        # Allow for small precision differences
        expected_duration = timedelta(minutes=5)
        actual_duration = log.duration
        self.assertAlmostEqual(
            actual_duration.total_seconds(), expected_duration.total_seconds(), places=0
        )

    def test_duration_property_unfinished(self):
        log = ProcessingLogFactory(finished_at=None)
        self.assertIsNone(log.duration)

    def test_running_queryset(self):
        running_log = ProcessingLogFactory(status="running")
        finished_log = ProcessingLogFactory(status="success")

        running_logs = ProcessingLog.objects.running()
        self.assertIn(running_log, running_logs)
        self.assertNotIn(finished_log, running_logs)

    def test_completed_queryset(self):
        running_log = ProcessingLogFactory(status="running")
        success_log = ProcessingLogFactory(status="success")
        failed_log = ProcessingLogFactory(status="failed")
        partial_log = ProcessingLogFactory(status="partial")

        completed_logs = ProcessingLog.objects.completed()
        self.assertNotIn(running_log, completed_logs)
        self.assertIn(success_log, completed_logs)
        self.assertIn(failed_log, completed_logs)
        self.assertIn(partial_log, completed_logs)

    def test_for_task_type_queryset(self):
        fetch_log = ProcessingLogFactory(task_type="fetch_articles")
        index_log = ProcessingLogFactory(task_type="index_articles")

        fetch_logs = ProcessingLog.objects.for_task_type("fetch_articles")
        self.assertIn(fetch_log, fetch_logs)
        self.assertNotIn(index_log, fetch_logs)

    def test_default_values(self):
        log = ProcessingLogFactory(result_data={}, command_args={})
        self.assertEqual(log.result_data, {})
        self.assertEqual(log.command_args, {})
        self.assertIsNotNone(log.started_at)


class SearchLogModelTest(TestCase):
    def test_str_representation(self):
        log = SearchLogFactory(query="This is a test query")
        self.assertEqual(str(log), "Search: This is a test query...")

    def test_str_representation_long_query(self):
        long_query = "This is a very long query that exceeds fifty characters and should be truncated"
        log = SearchLogFactory(query=long_query)
        expected = f"Search: {long_query[:50]}..."
        self.assertEqual(str(log), expected)

    def test_for_user_queryset(self):
        user1 = UserFactory()
        user2 = UserFactory()
        log1 = SearchLogFactory(user=user1)
        log2 = SearchLogFactory(user=user2)

        logs_for_user1 = SearchLog.objects.for_user(user1)
        self.assertIn(log1, logs_for_user1)
        self.assertNotIn(log2, logs_for_user1)

    def test_for_case_queryset(self):
        log1 = SearchLogFactory(case_id=123)
        log2 = SearchLogFactory(case_id=456)

        logs_for_case_123 = SearchLog.objects.for_case(123)
        self.assertIn(log1, logs_for_case_123)
        self.assertNotIn(log2, logs_for_case_123)

    def test_user_cascade_behavior(self):
        user = UserFactory()
        log = SearchLogFactory(user=user)

        user.delete()
        log.refresh_from_db()
        self.assertIsNone(log.user)  # Should be SET_NULL
