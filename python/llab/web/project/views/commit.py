from django import http
from django.shortcuts import get_object_or_404
from django.db.models import Q

from llab.web.project.models import Project, Commit


def get_commit_or_404(owner, project, commit):
    project = get_object_or_404(Project, name=project, owner__username=owner)
    try:
        sha1sum, branch = commit, commit
        q = (Q(project=project) &
            (Q(sha1sum=sha1sum) | Q(branch__name__endswith=branch)))
        return Commit.objects.filter(q).latest('id')
    except Commit.DoesNotExist:
        raise http.Http404('Commit or branch does not exist')


def commit_file(request, owner, project, commit, path):
    commit = get_commit_or_404(owner, project, commit)
    content, content_type = commit.fetch_blob(path)
    return http.HttpResponse(content, content_type=content_type)
