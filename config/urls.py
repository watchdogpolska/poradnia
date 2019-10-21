
from django.conf import settings
from django.urls import include, path
from django.conf.urls.static import static
from django.contrib import admin
from django.views.generic import TemplateView

admin.autodiscover()

urlpatterns = [
    path('',
        TemplateView.as_view(template_name='pages/home.html'),
        name="home"),
    path('admin/', admin.site.urls),
    path('navsearch/', include('poradnia.navsearch.urls', namespace="navsearch")),

    # User management
    path('uzytkownik/klucze', include('poradnia.keys.urls', namespace="keys")),
    path('uzytkownik/', include("poradnia.users.urls", namespace="users")),
    path('konta/', include('allauth.urls')),

    # Flatpages
    path('strony/', include('django.contrib.flatpages.urls')),
    path('tinymce/', include('tinymce.urls')),
    # Poradnia
    path('sprawy/', include('poradnia.cases.urls', namespace='cases')),
    path('listy/', include('poradnia.letters.urls', namespace='letters')),
    path('wydarzenia/', include('poradnia.events.urls', namespace='events')),
    path('porady/', include('poradnia.advicer.urls', namespace='advicer')),
    path('statystyki/', include('poradnia.stats.urls', namespace='stats')),
    path('uwagi/', include('poradnia.tasty_feedback.urls', namespace='tasty_feedback')),
    path('sprawy_sadowe/', include('poradnia.judgements.urls', namespace='judgements')),
    path('teryt/', include('poradnia.teryt.urls', namespace='teryt')),
    path('robots.txt', TemplateView.as_view(template_name='robots.txt')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]