from django.conf.urls import patterns, url

urlpatterns = patterns('organization.views',
    # Create a new organization by the authenticated user
    url(r'^account/organization/new/$',
        'organization_new', name='new'),

    # Manage the roles of the organization
    url(r'^(?P<organization>[\w-]+)/roles/$',
        'organization_roles', name='roles'),
)
