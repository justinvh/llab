import time

from django import http
from django.shortcuts import render, get_object_or_404

from .helpers import get_commit_or_404, project_page_context
from llab.web.project.models import Project, Branch
from llab.utils.collectiontools import DefaultOrderedDict
from llab.utils.git import commit_as_dict


def commit_list(request, owner, project, branch):
    branch = 'refs/heads/' + branch
    project = get_object_or_404(Project, name=project, owner__username=owner)
    branch = get_object_or_404(Branch, project=project, name=branch)
    project = branch.project
    owner = project.owner

    try:
        page = abs(int(request.GET.get('page', 1)))
    except ValueError:
        page = 1

    timelines = DefaultOrderedDict(list)
    last_t1 = None
    k, dt1, dt2 = 0, (page - 1) * 7, page * 7

    has_next = False
    has_prev = False
    next_page = page + 1
    prev_page = page - 1

    for commit in project.git.commits(branch=branch.name):
        t1 = time.strftime('%b %d, %Y', time.localtime(commit.commit_time))
        if last_t1 != t1:
            k += 1
            last_t1 = t1

        if k > dt1:
            timelines[t1].append(commit_as_dict(commit))
        else:
            has_prev = True

        if k >= dt2:
            has_next = True
            break

    context = {'owner': owner,
               'project': project,
               'branch': branch,
               'has_next': has_next,
               'has_prev': has_prev,
               'next_page': next_page,
               'prev_page': prev_page,
               'timelines': timelines.iteritems()}

    context.update(project_page_context(request, project))
    return render(request, 'project/commit/list.html', context)


def commit_view(request, owner, project, commit):
    commit = get_commit_or_404(owner, project, commit, try_hard=True)
    project = commit.project
    owner = project.owner
    context = {'owner': owner, 'project': project, 'commit': commit}
    context.update(project_page_context(request, project))
    return render(request, 'project/commit/view.html', context)


def commit_raw(request, owner, project, commit, path):
    """Display the raw file of a given commit.

    """
    commit = get_commit_or_404(owner, project, commit)
    content, content_type = commit.fetch_blob(path)
    return http.HttpResponse(content, content_type='text/plain')
