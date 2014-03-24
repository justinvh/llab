import misaka as m

from django import http
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils.safestring import mark_safe
from django.utils.encoding import force_unicode

from ..models import Project, Commit, Branch

misaka_extensions = m.EXT_FENCED_CODE


def lookup_and_guess_commit(project, sha1sum, try_hard=False):
    try:
        # First try to lookup by the existing commit in the project
        q = Q(project=project, sha1sum=sha1sum)
        return Commit.objects.filter(q).latest('commit_time')
    except Commit.DoesNotExist:
        pass

    try:
        # If that doesn't work then create it
        if try_hard:
            return Commit.get_or_create_from_sha(project, sha1sum)
    except Commit.DoesNotExist:
        pass

    try:
        # If that doesn't work then look up via a branch name
        refname = sha1sum
        q = Q(project=project)
        q &= (Q(name=refname) | Q(name='refs/heads/' + refname))
        branch = Branch.objects.filter(q).latest('id')
        return branch.ref
    except Branch.DoesNotExist:
        pass

    return None


def get_commit_or_404(owner, project, sha1sum, try_hard=False):
    project = get_object_or_404(Project, name=project, owner__username=owner)
    commit = lookup_and_guess_commit(project, sha1sum, try_hard)
    if not commit:
        raise http.Http404('{} was not found'.format(sha1sum))
    return commit


def safe_markdown(content):
    content = force_unicode(content)
    return mark_safe(m.html(content, extensions=misaka_extensions))


def project_page_context(request, project, branch=None):
    if branch is None:
        branch = Branch.objects.filter(project=project).earliest('id')
    return {'branch_count': project.branches.count(),
            'commit_count': branch.commit_count,
            'contributor_count': project.contributors.count(),
            'requirement_count': project.requirements.count(),
            'tag_count': project.tags.count(),
            'user_is_admin': project.is_admin(request.user)}
