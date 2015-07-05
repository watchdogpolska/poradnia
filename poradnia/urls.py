# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.conf.urls import patterns, include, url
from django.conf.urls.static import static

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
#    url(r'^$',  # noqa
#        TemplateView.as_view(template_name='pages/home.html'),
#        name="home"),
#    url(r'^about/$',
#        TemplateView.as_view(template_name='pages/about.html'),
#        name="about"),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),

    # User management
    url(r'^users/', include("users.urls", namespace="users")),
    url(r'^accounts/', include('allauth.urls')),

    # Uncomment the next line to enable avatars
    url(r'^avatar/', include('avatar.urls')),

    # Your stuff: custom urls go here
    url(r'^inbox/notifications/', include('notifications_custom.urls', namespace="notifications")),
    url(r'^', include('cases.urls', namespace='cases')),
    url(r'^letters/', include('letters.urls', namespace='letters')),
    url(r'^event/', include('events.urls', namespace='events')),
    url(r'^advice/', include('registers.urls', namespace='registers')),
    url(r'^autocomplete/', include('autocomplete_light.urls')),
) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += patterns('',
        url(r'^__debug__/', include(debug_toolbar.urls)),
    )
