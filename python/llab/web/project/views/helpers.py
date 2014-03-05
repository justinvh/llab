import misaka as m

from django import http
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils.safestring import mark_safe
from django.utils.encoding import force_unicode

from llab.web.project.models import Project, Commit

misaka_extensions = m.EXT_FENCED_CODE


def get_commit_or_404(owner, project, commit, try_hard=False):
    project = get_object_or_404(Project, name=project, owner__username=owner)
    try:
        sha1sum, branch = commit, commit
        q = (Q(project=project) &
            (Q(sha1sum=sha1sum) | Q(branch__name__endswith=branch)))
        return Commit.objects.filter(q).latest('commit_time')
    except Commit.DoesNotExist:
        if not try_hard:
            raise http.Http404('Commit or branch does not exist')
        return Commit.get_or_create_from_sha(project, commit, '?')


def safe_markdown(content):
    content = force_unicode(content)
    return mark_safe(m.html(content, extensions=misaka_extensions))


def project_page_context(request, project):
    return {'branch_count': project.branches.count(),
            'commit_count': project.commits.count(),
            'contributor_count': project.contributors.count(),
            'tag_count': project.tags.count(),
            'user_is_admin': project.is_admin(request.user)}

