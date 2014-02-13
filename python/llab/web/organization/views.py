from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from llab.utils.request import post_or_none

from .forms import OrganizationForm


@login_required
def organization_new(request):
    """Create a new organization.

    A user can create any organization, however they must be unique to the
    site. The organization names, much like the user names, are slug-based
    names.

    """
    post_data = post_or_none(request)
    form = OrganizationForm(post_data, prefix='organization')
    if post_data and form.is_valid():
        organization = form.save(owner=request.user)
        kwds = {'organization': organization.name}
        return redirect('organization:roles', kwargs=kwds)
    template = 'organization/new.html'
    context = {'form': form}
    return render(request, template, context)


@login_required
def organization_roles(request, organization):
    """Manages the roles of an organization.

    An organization can have multiple users with different roles. A role just
    defines a user's permission on the site. llab uses bitwise enumerations
    to define multiple roles.

    """
