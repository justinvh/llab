import user_streams

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from llab.utils.request import post_or_none

from .forms import ProjectForm
from .models import Project


@login_required
def project_index(request):
    newsfeed = user_streams.get_stream_items(request.user)
    newsfeed.update(seen=True)
    context = {'newsfeed': newsfeed}
    return render(request, 'project/index.html', context)


def project_new(request, owner=None, project=None):
    post_data = post_or_none(request)

    # We might be forking a new project, so check based on the URL requested
    fork = None
    if owner or project:
        fork = get_object_or_404(Project, owner=owner, project=project)

    # Attempt to validate the form and save against the fork specified
    project_form = ProjectForm(post_data)
    if post_data and project_form.is_valid():
        project = project_form.save(owner=request.user, fork=fork)
        return redirect(project)

    # The view will render notes about the fork if applicable
    context = {'form': project_form, 'fork': fork, 'owner': request.user}
    return render(request, 'project/new.html', context)


def project_view(request, owner, project):
    project = get_object_or_404(Project, name=project, owner__username=owner)
    context = {'project': project, 'owner': owner}
    if not project.commits.exists():
        return render(request, 'project/view-empty.html', context)
    context['commit'] = project.commits.latest('id')
    return render(request, 'project/view.html', context)
