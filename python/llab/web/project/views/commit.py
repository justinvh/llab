from django import http

from .helpers import get_commit_or_404


def commit_view(request):
    pass

def commit_raw(request, owner, project, commit, path):
    """Display the raw file of a given commit.

    """
    commit = get_commit_or_404(owner, project, commit)
    content, content_type = commit.fetch_blob(path)
    return http.HttpResponse(content, content_type='text/plain')
