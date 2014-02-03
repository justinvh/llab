from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^project/', include('project.urls', namespace='project')),
    url(r'^admin/', include(admin.site.urls)),

    (r'^accounts/login/$',
      'django.contrib.auth.views.login',
      {'template_name': 'accounts/login.html'}),

    (r'^accounts/login/$',
      'django.contrib.auth.views.logout',
      {'template_name': 'accounts/logout.html'}),
)
