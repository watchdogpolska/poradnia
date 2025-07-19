from django.contrib import admin

from .models import Article, ArticleChunk, ContentSource, ProcessingLog, SearchLog


@admin.register(ContentSource)
class ContentSourceAdmin(admin.ModelAdmin):
    list_display = ['name', 'base_url', 'is_active', 'last_sync', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'base_url']
    readonly_fields = ['created_at', 'last_sync']


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ['title', 'source', 'published_at', 'created_at']
    list_filter = ['source', 'published_at', 'created_at']
    search_fields = ['title', 'content']
    date_hierarchy = 'published_at'
    readonly_fields = ['created_at', 'updated_at']


class ArticleChunkInline(admin.TabularInline):
    model = ArticleChunk
    extra = 0
    readonly_fields = ['created_at']


@admin.register(ArticleChunk)
class ArticleChunkAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'article', 'chunk_index', 'token_count', 'created_at']
    list_filter = ['article__source', 'created_at']
    search_fields = ['content', 'article__title']
    readonly_fields = ['created_at']


@admin.register(ProcessingLog)
class ProcessingLogAdmin(admin.ModelAdmin):
    list_display = ['task_type', 'status', 'started_at', 'finished_at', 'duration']
    list_filter = ['task_type', 'status', 'started_at']
    search_fields = ['log_message']
    readonly_fields = ['task_type', 'status', 'started_at', 'finished_at', 'result_data', 
                       'sentry_event_id', 'log_message', 'command_args']
    
    def duration(self, obj):
        return obj.duration
    duration.short_description = 'Duration'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(SearchLog)
class SearchLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'query_short', 'results_count', 'response_time_ms', 'created_at']
    list_filter = ['user', 'created_at']
    search_fields = ['query']
    readonly_fields = ['user', 'query', 'case_id', 'results_count', 'response_time_ms', 'created_at']
    
    def query_short(self, obj):
        return f"{obj.query[:50]}..." if len(obj.query) > 50 else obj.query
    query_short.short_description = 'Query'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
