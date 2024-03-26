import logging
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import HttpResponseServerError
from django.template import loader
from django.urls import include, path
from django.views.generic import TemplateView

logger = logging.getLogger(__name__)

admin.autodiscover()

urlpatterns = [
    path("", TemplateView.as_view(template_name="pages/home.html"), name="home"),
    path("admin/", admin.site.urls),
    path("navsearch/", include("poradnia.navsearch.urls", namespace="navsearch")),
    # User management
    path("uzytkownik/klucze", include("poradnia.keys.urls", namespace="keys")),
    path("uzytkownik/", include("poradnia.users.urls", namespace="users")),
    path("konta/", include("allauth.urls")),
    # Poradnia
    path("sprawy/", include("poradnia.cases.urls", namespace="cases")),
    path("listy/", include("poradnia.letters.urls", namespace="letters")),
    path("wydarzenia/", include("poradnia.events.urls", namespace="events")),
    path("porady/", include("poradnia.advicer.urls", namespace="advicer")),
    path("uwagi/", include("poradnia.tasty_feedback.urls", namespace="tasty_feedback")),
    path("sprawy_sadowe/", include("poradnia.judgements.urls", namespace="judgements")),
    path("teryt/", include("poradnia.teryt.urls", namespace="teryt")),
    path("robots.txt", TemplateView.as_view(template_name="robots.txt")),
    path(
        "strony/regulamin-poradnictwa/",
        TemplateView.as_view(template_name="pages/terms.html"),
        name="terms",
    ),
    path(
        "strony/polityka-prywatnosci/",
        TemplateView.as_view(template_name="pages/privacy.html"),
        name="privacy",
    ),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if "rosetta" in settings.INSTALLED_APPS:
    urlpatterns += [path("rosetta/", include("rosetta.urls"))]

if settings.DEBUG:
    try:
        import debug_toolbar

        urlpatterns += [path("__debug__/", include(debug_toolbar.urls))]
    except ImportError:
        logger.warning("Could not import debug_toolbar.")


def handler500(request):
    """500 error handler which includes ``request`` in the context.

    Templates: `500.html`
    Context: None
    """

    t = loader.get_template("500.html")
    return HttpResponseServerError(t.render({"request": request}))
