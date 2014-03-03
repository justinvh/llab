from django.conf.urls import patterns, url

urlpatterns = patterns('project.views.project',
    # The newsfeed, etc.
    url(r'^$', 'project_index', name='index'),

    # Create a new project
    url(r'^new/', 'project_new', name='new'),

    # View the owner's referenced project
    url(r'^(?P<owner>[\w-]+)/(?P<project>[\w-]+)/$',
        'project_view', name='view'),

    # View the owner's referenced project
    url((r'^(?P<owner>[\w-]+)/(?P<project>[\w-]+)/tree/'
         r'(?P<commit>[\w]+)/(?P<path>.*)$'),
        'project_view', name='tree'),

    # View the owner's referenced project's commit tree
    url((r'^(?P<owner>[\w-]+)/(?P<project>[\w-]+)/json/tree/'
         r'(?P<commit>[\w]+)/(?P<path>[\w\/-]+)$'),
        'project_tree', name='tree'),

    # Fork an existing project
    url(r'^(?P<owner>[\w-]+)/(?P<project>[\w-]+)/fork$',
        'project_new', name='new'),

    # View the owner's referenced project
    url((r'^(?P<owner>[\w-]+)/(?P<project>[\w-]+)/commit/'
         r'(?P<commit>[\w]+)/$'),
        'project_view', name='commit'),
)
