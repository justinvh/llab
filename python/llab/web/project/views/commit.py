from django import http
from django.shortcuts import render

from .helpers import get_commit_or_404, project_page_context


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
