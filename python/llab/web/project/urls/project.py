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
         r'(?P<commit>refs/heads/[\w]+)/(?P<path>.*)$'),
        'project_view', name='tree'),

    # View the owner's referenced project
    url((r'^(?P<owner>[\w-]+)/(?P<project>[\w-]+)/tree/'
         r'(?P<commit>[\w]+)/(?P<path>.*)$'),
        'project_view', name='tree'),

    # View the owner's referenced project's commit tree
    url((r'^(?P<owner>[\w-]+)/(?P<project>[\w-]+)/json/tree/'
         r'(?P<commit>refs/heads/[\w]+)/(?P<path>[\w\/-]+)$'),
        'project_tree', name='json_tree_branch'),

    # View the owner's referenced project's commit tree
    url((r'^(?P<owner>[\w-]+)/(?P<project>[\w-]+)/json/tree/'
         r'(?P<commit>[\w]+)/(?P<path>[\w\/-]+)$'),
        'project_tree', name='json_tree'),

    # Fork an existing project
    url(r'^(?P<owner>[\w-]+)/(?P<project>[\w-]+)/fork/$',
        'project_new', name='new'),

    # List all the branches for a project
    url(r'^(?P<owner>[\w-]+)/(?P<project>[\w-]+)/branches/$',
        'project_branches', name='branches'),

    # List all the tags for a project
    url(r'^(?P<owner>[\w-]+)/(?P<project>[\w-]+)/tags/$',
        'project_tags', name='tags'),

    # Download
    url((r'^(?P<owner>[\w-]+)/(?P<project>[\w-]+)/tag/'
         r'(?P<tag>.*)/download/$'),
        'project_download', name='download'),

    # View a readme for a particular directory
    url((r'^(?P<owner>[\w-]+)/(?P<project>[\w-]+)/readme/'
         r'(?P<commit>[\w]+)/(?P<directory>[\w\/-]+)$'),
        'project_readme', name='readme'),

    # View a readme for a top-level commit
    url((r'^(?P<owner>[\w-]+)/(?P<project>[\w-]+)/readme/'
         r'(?P<commit>[\w]+)/$'),
        'project_readme', name='readme_toplevel'),
)
