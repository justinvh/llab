from django.conf.urls import patterns, include, url

urlpatterns = patterns('project.views',
    # Create a new project
    url(r'^new/', 'project_new', name='new'),

    # Fork an existing project
    url(r'^(?P<owner>[\w-]+)/(?P<project>[\w-]+)/fork$',
        'project_new', name='new'),

    # View the owner's referenced project
    url(r'^(?P<owner>[\w-]+)/(?P<project>[\w-]+)$',
        'project_view', name='view')
)
