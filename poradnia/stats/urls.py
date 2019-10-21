from django.urls import path
from django.utils.translation import ugettext_lazy as _

from . import views

urlpatterns = [
    path("", views.StatsIndexView.as_view(), name="index"),
    path(
        "api/sprawy/czas_reakcji",
        views.StatsCaseReactionApiView.as_view(),
        name="case_reaction_api",
    ),
    path(
        "api/sprawy/utworzone",
        views.StatsCaseCreatedApiView.as_view(),
        name="case_created_api",
    ),
    path(
        "api/sprawy/bez_odpowiedzi",
        views.StatsCaseUnansweredApiView.as_view(),
        name="case_unanswered_api",
    ),
    path(
        "api/listy/utworzone",
        views.StatsLetterCreatedApiView.as_view(),
        name="letter_created_api",
    ),
    path(
        "api/uzytkownicy/zarejestrowani",
        views.StatsUserRegisteredApiView.as_view(),
        name="user_registered_api",
    ),
    path(
        "render/sprawy/utworzone",
        views.StatsCaseCreatedRenderView.as_view(),
        name="case_created_render",
    ),
    path(
        "render/sprawy/czas_reakcji",
        views.StatsCaseReactionRenderView.as_view(),
        name="case_reaction_render",
    ),
    path(
        "render/sprawy/bez_odpowiedzi",
        views.StatsCaseUnansweredRenderView.as_view(),
        name="case_unanswered_render",
    ),
    path(
        "render/listy/utworzone",
        views.StatsLetterCreatedRenderView.as_view(),
        name="letter_created_render",
    ),
    path(
        "render/uzytkownicy/zarejestrowani",
        views.StatsUserRegisteredRenderView.as_view(),
        name="user_registered_render",
    ),
    path("sprawy/utworzone", views.StatsCaseCreatedView.as_view(), name="case_created"),
    path(
        "sprawy/czas_reakcji",
        views.StatsCaseReactionView.as_view(),
        name="case_reaction",
    ),
    path(
        "sprawy/bez_odpowiedzi",
        views.StatsCaseUnansweredView.as_view(),
        name="case_unanswered",
    ),
    path(
        "listy/utworzone", views.StatsLetterCreatedView.as_view(), name="letter_created"
    ),
    path(
        "uzytkownicy/zarejestrowani",
        views.StatsUserRegisteredView.as_view(),
        name="user_registered",
    ),
    path(
        _("item-<slug:key>/"), views.ValueBrowseListView.as_view(), name="item_detail"
    ),
    path(
        _("item-<slug:key>/<month>/<int:year>/~csv"),
        views.CSVValueListView.as_view(),
        name="item_detail_csv",
    ),
    path(
        _("item-<slug:key>/<month>/<int:year>/~json"),
        views.JSONValueListView.as_view(),
        name="item_detail_json",
    ),
    path(
        _("item-<slug:key>/<month>/<int:year>"),
        views.ValueBrowseListView.as_view(),
        name="item_detail",
    ),
    path(_("graph-<int:pk>"), views.GraphDetailView.as_view(), name="graph_detail"),
    path(
        _("graph-<int:pk>/<int:month>/<int:year>"),
        views.GraphDetailView.as_view(),
        name="graph_detail",
    ),
    path(
        _("graph-<int:pk>/<int:month>/<int:year>/~json"),
        views.JSONGraphDetailView.as_view(),
        name="graph_detail_json",
    ),
]

app_name = "poradnia.stats"
