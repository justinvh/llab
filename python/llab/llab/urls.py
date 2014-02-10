from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^account/', include('account.urls', namespace='account')),
    url(r'^', include('project.urls', namespace='project')),
    url(r'^', include('organization.urls', namespace='organization')),
)
