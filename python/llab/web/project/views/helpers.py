import misaka as m

from django import http
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils.safestring import mark_safe
from django.utils.encoding import force_unicode

from llab.web.project.models import Project, Commit, Branch

misaka_extensions = m.EXT_FENCED_CODE


def get_commit_or_404(owner, project, sha1sum, try_hard=False):
    project = get_object_or_404(Project, name=project, owner__username=owner)
    try:
        q = Q(project=project, sha1sum=sha1sum)
        return Commit.objects.filter(q).latest('commit_time')
    except Commit.DoesNotExist:
        if not try_hard:
            raise http.Http404('Commit does not exist')
        return Commit.get_or_create_from_sha(project, sha1sum)


def safe_markdown(content):
    content = force_unicode(content)
    return mark_safe(m.html(content, extensions=misaka_extensions))


def project_page_context(request, project, branch='refs/heads/master'):
    branch = Branch.objects.get(project=project, name=branch)
    return {'branch_count': project.branches.count(),
            'commit_count': branch.commit_count,
            'contributor_count': project.contributors.count(),
            'tag_count': project.tags.count(),
            'user_is_admin': project.is_admin(request.user)}
