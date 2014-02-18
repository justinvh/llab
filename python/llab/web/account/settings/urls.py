from django.conf.urls import patterns, url

urlpatterns = patterns('views',
    # The overall settings
    url(r'^profile/$', 'settings_profile', name='profile'),

    # Manage the user's account keys
    url(r'^ssh/$', 'settings_ssh', name='ssh'),
)
