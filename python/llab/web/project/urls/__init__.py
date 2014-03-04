from django.conf.urls import patterns, url, include

from .project import urlpatterns

urlpatterns += patterns('',
    url(r'^', include('project.urls.commit', namespace='commit'))
)
