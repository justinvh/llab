import os
import user_streams

from django.db import models, transaction
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.template.loader import render_to_string

from llab import settings
from utils.enumeration import make_bitwise_enumeration, BitwiseSet
from utils.git import Git

Permission = make_bitwise_enumeration(
    'Permission', ('download_code', 'fork_project', 'read_project',
                   'read_wiki', 'read_issue', 'read_milestone',
                   'read_project_snippet', 'read_team_member',
                   'read_merge_request', 'read_note', 'write_issue',
                   'write_not'))


class Project(models.Model):
    owner = models.ForeignKey(User, related_name='projects_managed')
    fork = models.ForeignKey('Project', related_name='forks', null=True)
    private = models.BooleanField(default=False)
    name = models.SlugField()
    description = models.CharField(max_length=255)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    starred_by = models.ManyToManyField(User)

    @property
    def git(self):
        if hasattr(self, '_git'):
            return self._git
        self._git = Git(path=self.get_absolute_path())
        return self._git

    @git.setter
    def git(self, value):
        self._git = value

    def star(self, user):
        template = 'project/activity-feed/star.html'
        context = {'user': user, 'project': self}
        content = render_to_string(template, context)
        user_streams.add_stream_item(user, content)
        self.starred_by.add(user)
        return content

    def unstar(self, user):
        self.starred_by.remove(user)

    def branch_add(self, branch_name):
        template = 'project/activity-feed/branch-add.html'
        context = {'project': self, 'branch': branch_name}
        content = render_to_string(template, context)
        user_streams.add_stream_item(self.starred_by.all(), content)
        return content

    def branch_remove(self, branch_name):
        template = 'project/activity-feed/branch-remove.html'
        context = {'project': self, 'branch': branch_name}
        content = render_to_string(template, context)
        user_streams.add_stream_item(self.starred_by.all(), content)
        return content

    def get_absolute_url(self):
        kwds = {'owner': self.owner.username, 'name': self.name}
        return reverse('view', kwargs=kwds, current_app='project')

    def get_absolute_path(self):
        repo = settings.GIT_REPOSITORY_PATH
        return os.path.join(repo, self.full_name())

    @transaction.atomic
    def save(self, *args, **kwargs):
        create_project = True if not self.pk else False
        super(Project, self).save(*args, **kwargs)
        if create_project:
            self.create_project()

    def create_project(self):
        clone = self.fork.get_absolute_path() if self.fork else None
        project_path = self.get_absolute_path()
        self.git = Git.clone_or_create(path=project_path, clone=clone)

    def full_name(self):
        return os.path.join(self.owner.username, self.name)

    def __unicode__(self):
        self.full_name()


class Group(models.Model):
    name = models.CharField(max_length=255)
    _permissions = models.IntegerField()

    @property
    def permissions(self):
        return BitwiseSet(self, '_permission_mapping', Permission)
        if hasattr(self, '_permission_mapping'):
            return self._permission_mapping
        self._permission_mapping = BitwiseSet(Permission, self, '_permissions')
        for permission, value in Permission.choices:
            if self._permissions & value:
                self._permission_mapping.add(getattr(Permission, permission))
        return self._permission_mapping

    @permissions.setter
    def permissions(self, permission_set):
        self._permissions = 0
        for value in permission_set:
            self._permissions |= value


class Role(models.Model):
    user = models.ForeignKey(User, related_name='+')
    project = models.ForeignKey(Project, related_name='roles')
    group = models.ForeignKey(Group, related_name='+')
