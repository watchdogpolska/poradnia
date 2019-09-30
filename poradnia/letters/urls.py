from django.conf.urls import url
from django.views.decorators.csrf import csrf_exempt

from . import views

urlpatterns = [
    url(r'^$', views.NewCaseCreateView.as_view(), name='home'),
    url(r'^$', views.NewCaseCreateView.as_view(), name='add'),
    url(r'^rejestr$', views.LetterListView.as_view(), name='list'),
    url(r'^sprawa-(?P<case_pk>\d+)/$', views.add, name="add"),
    url(r'^sprawa-(?P<case_pk>\d+)/list-(?P<letter_pk>\d+)/zalaczniki$', views.StreamAttachmentView.as_view(), name="attachments_zip"),
    url(r'^(?P<pk>\d+)/wyslij/$', views.send, name="send"),
    url(r'^(?P<pk>\d+)/edytuj/$', views.LetterUpdateView.as_view(), name="edit"),
    url(r'^(?P<pk>\d+)/$', views.send, name="detail"),
    url(r'^webhook',
        csrf_exempt(views.ReceiveEmailView.as_view()),
        name="webhook"
),

]
