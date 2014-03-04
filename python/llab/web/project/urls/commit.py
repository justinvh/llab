from django.conf.urls import patterns, url


# Commit related URL patterns
urlpatterns = patterns('project.views.commit',

    # View the details of a commit
    url((r'^(?P<owner>[\w-]+)/(?P<project>[\w-]+)/commit/'
         r'(?P<commit>[\w]+)/$'),
         'commit_view', name='commit:view'),

    # View the raw file for a commit
    url((r'^(?P<owner>[\w-]+)/(?P<project>[\w-]+)/raw/'
         r'(?P<commit>[\w]+)/(?P<path>.*)$'),
         'commit_raw', name='commit:raw'),
)
