from django import http

from .helpers import get_commit_or_404


def commit_file(request, owner, project, commit, path):
    commit = get_commit_or_404(owner, project, commit)
    content, content_type = commit.fetch_blob(path)
    return http.HttpResponse(content, content_type='text/plain')
