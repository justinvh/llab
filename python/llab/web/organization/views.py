from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import models, transaction

from llab.utils.request import post_or_none

from .forms import OrganizationForm, RoleForm
from .models import Organization, Group


@login_required
@transaction.atomic
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
        Group.create_builtins(organization)
        return redirect(organization.get_role_management_absolute_url())
    template = 'organization/new.html'
    context = {'form': form}
    return render(request, template, context)


@login_required
@transaction.atomic
def organization_roles(request, organization):
    """Manages the roles of an organization.

    An organization can have multiple users with different roles. A role just
    defines a user's permission on the site. llab uses bitwise enumerations
    to define multiple roles.

    """
    organization = get_object_or_404(Organization, name=organization)
    post_data = post_or_none(request)
    form = RoleForm(organization, post_data, prefix='role')
    if post_data and form.is_valid():
        form.save()
        return reverse(organization.get_role_management_absolute_url())
    template = 'organization/roles.html'
    context = {'form': form, 'organization': organization}
    return render(request, template, context)
