from django.db import models
from django.db.models.query import QuerySet
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from poradnia.users.models import User


class ContentSourceQuerySet(QuerySet):
    def active(self):
        return self.filter(is_active=True)


class ContentSource(models.Model):
    """Model to track article sources with API endpoints and sync status."""

    name = models.CharField(max_length=100, verbose_name=_("Name"))
    base_url = models.URLField(verbose_name=_("Base URL"))
    api_endpoint = models.URLField(verbose_name=_("API endpoint"))
    is_active = models.BooleanField(default=True, verbose_name=_("Is active"))
    last_sync = models.DateTimeField(null=True, blank=True, verbose_name=_("Last sync"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created at"))

    objects = ContentSourceQuerySet.as_manager()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Content source")
        verbose_name_plural = _("Content sources")


class ArticleQuerySet(QuerySet):
    def published(self):
        return self.filter(published_at__isnull=False)

    def for_source(self, source):
        return self.filter(source=source)


class Article(models.Model):
    """Model to store article content with metadata and relationships."""

    source = models.ForeignKey(
        ContentSource,
        on_delete=models.CASCADE,
        related_name="articles",
        verbose_name=_("Source"),
    )
    external_id = models.CharField(max_length=100, verbose_name=_("External ID"))
    title = models.CharField(max_length=500, verbose_name=_("Title"))
    content = models.TextField(verbose_name=_("Content"))
    excerpt = models.TextField(blank=True, verbose_name=_("Excerpt"))
    url = models.URLField(verbose_name=_("URL"))
    published_at = models.DateTimeField(
        null=True, blank=True, verbose_name=_("Published at")
    )
    modified_at = models.DateTimeField(
        null=True, blank=True, verbose_name=_("Modified at")
    )
    categories = models.JSONField(default=list, verbose_name=_("Categories"))
    tags = models.JSONField(default=list, verbose_name=_("Tags"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created at"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated at"))

    objects = ArticleQuerySet.as_manager()

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = _("Article")
        verbose_name_plural = _("Articles")
        unique_together = [["source", "external_id"]]
        ordering = ["-published_at"]


class ArticleChunkQuerySet(QuerySet):
    def for_article(self, article):
        return self.filter(article=article)

    def with_embeddings(self):
        return self.filter(embedding__isnull=False)


class ArticleChunk(models.Model):
    """Model for text segmentation with vector embeddings."""

    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name="chunks",
        verbose_name=_("Article"),
    )
    chunk_index = models.PositiveIntegerField(verbose_name=_("Chunk index"))
    content = models.TextField(verbose_name=_("Content"))
    embedding = models.JSONField(null=True, blank=True, verbose_name=_("Embedding"))
    token_count = models.PositiveIntegerField(
        null=True, blank=True, verbose_name=_("Token count")
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created at"))

    objects = ArticleChunkQuerySet.as_manager()

    def __str__(self):
        return f"{self.article.title} - Chunk {self.chunk_index}"

    class Meta:
        verbose_name = _("Article chunk")
        verbose_name_plural = _("Article chunks")
        unique_together = [["article", "chunk_index"]]
        ordering = ["article", "chunk_index"]


class ProcessingLogQuerySet(QuerySet):
    def running(self):
        return self.filter(status="running")

    def completed(self):
        return self.filter(status__in=["success", "failed", "partial"])

    def for_task_type(self, task_type):
        return self.filter(task_type=task_type)


class ProcessingLog(models.Model):
    """Model for batch job monitoring with detailed status tracking."""

    TASK_TYPE = models.TextChoices(
        "TASK_TYPE",
        [
            ("fetch_articles", _("Fetch articles")),
            ("index_articles", _("Index articles")),
            ("generate_embeddings", _("Generate embeddings")),
            ("reindex_all", _("Full reindexing")),
            ("cleanup_orphaned", _("Cleanup orphaned records")),
        ],
    )

    STATUS = models.TextChoices(
        "STATUS",
        [
            ("running", _("Running")),
            ("success", _("Success")),
            ("failed", _("Failed")),
            ("partial", _("Partial success")),
        ],
    )

    task_type = models.CharField(
        max_length=50, choices=TASK_TYPE.choices, verbose_name=_("Task type")
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS.choices,
        default="running",
        verbose_name=_("Status"),
    )
    started_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Started at"))
    finished_at = models.DateTimeField(
        null=True, blank=True, verbose_name=_("Finished at")
    )
    result_data = models.JSONField(default=dict, verbose_name=_("Result data"))
    sentry_event_id = models.CharField(
        max_length=100, null=True, blank=True, verbose_name=_("Sentry event ID")
    )
    log_message = models.TextField(blank=True, verbose_name=_("Log message"))
    command_args = models.JSONField(default=dict, verbose_name=_("Command arguments"))

    objects = ProcessingLogQuerySet.as_manager()

    @property
    def duration(self):
        """Calculate task duration if finished."""
        if self.finished_at and self.started_at:
            return self.finished_at - self.started_at
        return None

    def __str__(self):
        return f"{self.get_task_type_display()} - {self.get_status_display()}"

    class Meta:
        verbose_name = _("Processing log")
        verbose_name_plural = _("Processing logs")
        ordering = ["-started_at"]


class SearchLogQuerySet(QuerySet):
    def for_user(self, user):
        return self.filter(user=user)

    def for_case(self, case_id):
        return self.filter(case_id=case_id)


class SearchLog(models.Model):
    """Model for search analytics with performance metrics."""

    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("User")
    )
    query = models.TextField(verbose_name=_("Query"))
    case_id = models.PositiveIntegerField(
        null=True, blank=True, verbose_name=_("Case ID")
    )
    results_count = models.PositiveIntegerField(verbose_name=_("Results count"))
    response_time_ms = models.PositiveIntegerField(verbose_name=_("Response time (ms)"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created at"))

    objects = SearchLogQuerySet.as_manager()

    def __str__(self):
        return f"Search: {self.query[:50]}..."

    class Meta:
        verbose_name = _("Search log")
        verbose_name_plural = _("Search logs")
        ordering = ["-created_at"]
