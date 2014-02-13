from django.conf.urls import patterns, url

urlpatterns = patterns('views',
    # Manage the user's account keys
    url(r'^ssh/$', 'settings_ssh', name='ssh'),
)
