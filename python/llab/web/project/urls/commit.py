"""
The Project apps namespaces 'commit' related views for
sake of organization.

"""
from django.conf.urls import patterns, url


# Commit related URL patterns
urlpatterns = patterns('project.views.commit',

    # List all the commits
    url((r'^(?P<owner>[\w-]+)/(?P<project>[\w-]+)/commits/'
         r'(?P<branch>refs/heads/[\w]+)/$'),
         'commit_list', name='list'),

    # List all the commits
    url((r'^(?P<owner>[\w-]+)/(?P<project>[\w-]+)/commits/'
         r'(?P<branch>[\w]+)/$'),
         'commit_list', name='list'),

    # View the details of a commit
    url((r'^(?P<owner>[\w-]+)/(?P<project>[\w-]+)/commit/'
         r'(?P<commit>[\w]+)/$'),
         'commit_view', name='view'),

    # Compute the revision tree for a given Commit path
    url((r'^(?P<owner>[\w-]+)/(?P<project>[\w-]+)/commit/'
         r'(?P<commit>[\w]+)/revtree/(?P<directory>.*)$'),
         'commit_revtree', name='revtree'),

    # View the raw file for a commit
    url((r'^(?P<owner>[\w-]+)/(?P<project>[\w-]+)/raw/'
         r'(?P<commit>[\w]+)/(?P<path>.*)$'),
         'commit_raw', name='raw'),
)
