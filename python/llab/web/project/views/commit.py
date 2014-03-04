from django import http
from django.shortcuts import render

from .helpers import get_commit_or_404


def commit_view(request, owner, project, commit):
    commit = get_commit_or_404(owner, project, commit)
    context = {'owner': owner, 'project': project, 'commit': commit}
    return render(request, 'project/commit/view.html', context)


def commit_raw(request, owner, project, commit, path):
    """Display the raw file of a given commit.

    """
    commit = get_commit_or_404(owner, project, commit)
    content, content_type = commit.fetch_blob(path)
    return http.HttpResponse(content, content_type='text/plain')
