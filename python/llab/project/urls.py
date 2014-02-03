from django.conf.urls import patterns, url

urlpatterns = patterns('project.views',
    # The newsfeed, etc.
    url(r'^$', 'project_index', name='index'),

    # Create a new project
    url(r'^new/', 'project_new', name='new'),

    # Fork an existing project
    url(r'^(?P<owner>[\w-]+)/(?P<project>[\w-]+)/fork$',
        'project_new', name='new'),

    # View the owner's referenced project
    url(r'^(?P<owner>[\w-]+)/(?P<project>[\w-]+)$',
        'project_view', name='view')
)
