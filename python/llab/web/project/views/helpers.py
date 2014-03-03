import markdown2

from django import http
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils.safestring import mark_safe
from django.utils.encoding import force_unicode

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


def safe_markdown(content):
    content = force_unicode(content)
    md = markdown2.markdown(content, safe_mode=True)
    return mark_safe(md)
