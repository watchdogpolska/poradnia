from django.contrib.admin.sites import AdminSite
from django.test import TestCase

from poradnia.knowledge.admin import (
    ArticleAdmin,
    ArticleChunkAdmin,
    ContentSourceAdmin,
    ProcessingLogAdmin,
    SearchLogAdmin,
)
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


class AdminTestCase(TestCase):
    def setUp(self):
        self.site = AdminSite()


class ContentSourceAdminTest(AdminTestCase):
    def test_list_display(self):
        admin = ContentSourceAdmin(ContentSource, self.site)
        expected = ["name", "base_url", "is_active", "last_sync", "created_at"]
        self.assertEqual(admin.list_display, expected)

    def test_list_filter(self):
        admin = ContentSourceAdmin(ContentSource, self.site)
        expected = ["is_active", "created_at"]
        self.assertEqual(admin.list_filter, expected)

    def test_search_fields(self):
        admin = ContentSourceAdmin(ContentSource, self.site)
        expected = ["name", "base_url"]
        self.assertEqual(admin.search_fields, expected)

    def test_readonly_fields(self):
        admin = ContentSourceAdmin(ContentSource, self.site)
        expected = ["created_at", "last_sync"]
        self.assertEqual(admin.readonly_fields, expected)


class ArticleAdminTest(AdminTestCase):
    def test_list_display(self):
        admin = ArticleAdmin(Article, self.site)
        expected = ["title", "source", "published_at", "created_at"]
        self.assertEqual(admin.list_display, expected)

    def test_list_filter(self):
        admin = ArticleAdmin(Article, self.site)
        expected = ["source", "published_at", "created_at"]
        self.assertEqual(admin.list_filter, expected)

    def test_search_fields(self):
        admin = ArticleAdmin(Article, self.site)
        expected = ["title", "content"]
        self.assertEqual(admin.search_fields, expected)

    def test_date_hierarchy(self):
        admin = ArticleAdmin(Article, self.site)
        self.assertEqual(admin.date_hierarchy, "published_at")

    def test_readonly_fields(self):
        admin = ArticleAdmin(Article, self.site)
        expected = ["created_at", "updated_at"]
        self.assertEqual(admin.readonly_fields, expected)


class ArticleChunkAdminTest(AdminTestCase):
    def test_list_display(self):
        admin = ArticleChunkAdmin(ArticleChunk, self.site)
        expected = ["__str__", "article", "chunk_index", "token_count", "created_at"]
        self.assertEqual(admin.list_display, expected)

    def test_list_filter(self):
        admin = ArticleChunkAdmin(ArticleChunk, self.site)
        expected = ["article__source", "created_at"]
        self.assertEqual(admin.list_filter, expected)

    def test_search_fields(self):
        admin = ArticleChunkAdmin(ArticleChunk, self.site)
        expected = ["content", "article__title"]
        self.assertEqual(admin.search_fields, expected)


class ProcessingLogAdminTest(AdminTestCase):
    def test_list_display(self):
        admin = ProcessingLogAdmin(ProcessingLog, self.site)
        expected = ["task_type", "status", "started_at", "finished_at", "duration"]
        self.assertEqual(admin.list_display, expected)

    def test_list_filter(self):
        admin = ProcessingLogAdmin(ProcessingLog, self.site)
        expected = ["task_type", "status", "started_at"]
        self.assertEqual(admin.list_filter, expected)

    def test_search_fields(self):
        admin = ProcessingLogAdmin(ProcessingLog, self.site)
        expected = ["log_message"]
        self.assertEqual(admin.search_fields, expected)

    def test_readonly_fields(self):
        admin = ProcessingLogAdmin(ProcessingLog, self.site)
        expected = [
            "task_type",
            "status",
            "started_at",
            "finished_at",
            "result_data",
            "sentry_event_id",
            "log_message",
            "command_args",
        ]
        self.assertEqual(admin.readonly_fields, expected)

    def test_no_add_permission(self):
        admin = ProcessingLogAdmin(ProcessingLog, self.site)
        self.assertFalse(admin.has_add_permission(None))

    def test_no_change_permission(self):
        admin = ProcessingLogAdmin(ProcessingLog, self.site)
        self.assertFalse(admin.has_change_permission(None))

    def test_duration_method(self):
        admin = ProcessingLogAdmin(ProcessingLog, self.site)
        log = ProcessingLogFactory()
        result = admin.duration(log)
        self.assertEqual(result, log.duration)


class SearchLogAdminTest(AdminTestCase):
    def test_list_display(self):
        admin = SearchLogAdmin(SearchLog, self.site)
        expected = [
            "user",
            "query_short",
            "results_count",
            "response_time_ms",
            "created_at",
        ]
        self.assertEqual(admin.list_display, expected)

    def test_list_filter(self):
        admin = SearchLogAdmin(SearchLog, self.site)
        expected = ["user", "created_at"]
        self.assertEqual(admin.list_filter, expected)

    def test_search_fields(self):
        admin = SearchLogAdmin(SearchLog, self.site)
        expected = ["query"]
        self.assertEqual(admin.search_fields, expected)

    def test_readonly_fields(self):
        admin = SearchLogAdmin(SearchLog, self.site)
        expected = [
            "user",
            "query",
            "case_id",
            "results_count",
            "response_time_ms",
            "created_at",
        ]
        self.assertEqual(admin.readonly_fields, expected)

    def test_no_add_permission(self):
        admin = SearchLogAdmin(SearchLog, self.site)
        self.assertFalse(admin.has_add_permission(None))

    def test_no_change_permission(self):
        admin = SearchLogAdmin(SearchLog, self.site)
        self.assertFalse(admin.has_change_permission(None))

    def test_query_short_method(self):
        admin = SearchLogAdmin(SearchLog, self.site)

        # Test short query
        short_log = SearchLogFactory(query="Short query")
        result = admin.query_short(short_log)
        self.assertEqual(result, "Short query")

        # Test long query
        long_query = "This is a very long query that definitely exceeds fifty characters and should be truncated"
        long_log = SearchLogFactory(query=long_query)
        result = admin.query_short(long_log)
        expected = f"{long_query[:50]}..."
        self.assertEqual(result, expected)
