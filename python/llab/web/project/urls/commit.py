from django.conf.urls import patterns, url


# Commit related URL patterns
urlpatterns = patterns('project.views.commit',

    # View the file referenced project
    url((r'^(?P<owner>[\w-]+)/(?P<project>[\w-]+)/commit/'
         r'(?P<commit>[\w]+)/(?P<path>.*)$'),
        'commit_file', name='file_for_commit'),
)
