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

    # View a readme for a particular directory
    url((r'^(?P<owner>[\w-]+)/(?P<project>[\w-]+)/readme/'
         r'(?P<commit>[\w]+)/(?P<directory>[\w\/-]+)$'),
        'project_readme', name='readme'),

    url((r'^(?P<owner>[\w-]+)/(?P<project>[\w-]+)/readme/'
         r'(?P<commit>[\w]+)/$'),
        'project_readme', name='readme_toplevel'),
)
