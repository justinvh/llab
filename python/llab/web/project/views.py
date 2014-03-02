import user_streams
import json

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django import http
from django.db.models import Q

from llab.utils.request import post_or_none

from .forms import ProjectForm
from .models import Project, Commit


@login_required
def project_index(request):
    newsfeed = user_streams.get_stream_items(request.user)
    newsfeed_new = list(newsfeed.filter(seen=False))
    newsfeed_old = list(newsfeed.filter(seen=True)[:10])
    newsfeed.update(seen=True)
    context = {'newsfeed_old': newsfeed_old,
               'newsfeed_new': newsfeed_new}
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


def project_view(request, owner, project, commit=None, path=None):
    project = get_object_or_404(Project, name=project, owner__username=owner)
    context = {'project': project, 'owner': owner}

    if not project.commits.exists():
        return render(request, 'project/view-empty.html', context)

    if commit:
        try:
            sha1sum, branch = commit, commit
            q = (Q(project=project) &
                 (Q(sha1sum=sha1sum) | Q(branch__name__endswith=branch)))
            commit = Commit.objects.filter(q).latest('id')
        except Commit.DoesNotExist:
            raise http.Http404('Commit or branch does not exist')
    else:
        commit = project.commits.latest('id')

    if path:
        tree = commit.tree
        for item in path.split('/')[:-1]:
            new_tree = tree.get(item)
            if new_tree and new_tree['type'] == 'folder':
                tree = new_tree['tree']
            elif new_tree and new_tree['type'] == 'file':
                raise http.Http404('Filepaths are not supported')
            else:
                raise http.Http404('Path not found')
    else:
        path = project.name

    context.update({'commit': commit,
                    'branch_count': project.branches.count(),
                    'commit_count': project.commits.count(),
                    'contributor_count': project.contributors.count(),
                    'tag_count': project.tags.count(),
                    'current_path': path,
                    'user_is_admin': project.is_admin(request.user)})

    return render(request, 'project/view.html', context)


def project_tree(request, owner, project, commit, path):
    project = get_object_or_404(Project, name=project, owner__username=owner)
    try:
        sha1sum, branch = commit, commit
        q = (Q(project=project) &
            (Q(sha1sum=sha1sum) | Q(branch__name__endswith=branch)))
        commit = Commit.objects.filter(q).latest('id')
        content = json.dumps({'tree': commit.tree, 'path': path})
        return http.HttpResponse(content, content_type='application/json')
    except Commit.DoesNotExist:
        raise http.Http404('Commit or branch does not exist')
