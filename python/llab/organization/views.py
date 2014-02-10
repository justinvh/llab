from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from utils.request import post_or_none

from .forms import OrganizationForm


@login_required
def organization_new(request):
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
    pass
