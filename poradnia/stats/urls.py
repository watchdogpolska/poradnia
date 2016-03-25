from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.StatsIndexView.as_view(), name="index"),
    url(r'^api/sprawy/czas_reakcji$', views.StatsCaseReactionApiView.as_view(), name="case_stats_reaction_api"),
    url(r'^api/sprawy/utworzone$', views.StatsCaseCreatedApiView.as_view(), name="case_stats_created_api"),
    url(r'^api/sprawy/bez_odpowiedzi$', views.StatsCaseUnansweredApiView.as_view(), name="case_stats_unanswered_api"),
    url(r'^render/sprawy/utworzone$', views.StatsCaseCreatedRenderView.as_view(), name="case_stats_created_render"),
    url(r'^render/sprawy/czas_reakcji$', views.StatsCaseReactionRenderView.as_view(), name="case_stats_reaction_render"),
    url(r'^sprawy/utworzone$', views.StatsCaseCreatedView.as_view(), name="case_stats_created"),
    url(r'^sprawy/czas_reakcji$', views.StatsCaseReactionView.as_view(), name="case_stats_reaction"),
]
