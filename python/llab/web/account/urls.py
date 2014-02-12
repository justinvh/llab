from django.conf.urls import patterns, url

urlpatterns = patterns('account.views',
    # Django handles the other "account" views
    url(r'^join/$', 'account_join', name='join'),
)

urlpatterns += patterns('',
    url(r'^login/$', 'django.contrib.auth.views.login',
        {'template_name': 'account/login.html'}, name='login'),

    url(r'^logout/$', 'django.contrib.auth.views.logout',
        {'template_name': 'account/logout.html'}, name='logout'),
)
