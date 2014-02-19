from django.conf.urls import patterns, url

urlpatterns = patterns('account.settings.views',
    # The overall settings
    url(r'^profile/$', 'settings_profile', name='profile'),

    # Manage the user's account keys
    url(r'^ssh/$', 'settings_ssh', name='ssh'),

    # Delete a key
    url(r'^ssh/(?P<public_key_pk>\d+)/delete/$',
        'settings_ssh_delete', name='ssh_delete'),
)
