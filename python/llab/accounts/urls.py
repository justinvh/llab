from django.conf.urls import patterns, url

urlpatterns = patterns('accounts.views',
    # Django handles the other "accounts" views
    url(r'^register/$', 'accounts_register', name='register'),
)

urlpatterns += patterns('',
    url(r'^login/$', 'django.contrib.auth.views.login',
        {'template_name': 'accounts/login.html'}, name='login'),

    url(r'^logout/$', 'django.contrib.auth.views.logout',
        {'template_name': 'accounts/logout.html'}, name='logout'),
)
