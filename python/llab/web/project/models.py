import os

import django.dispatch

from django.db import models, transaction
from django.core.urlresolvers import reverse
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext as _

from django.conf import settings
from llab.utils.git import Git
from llab.utils.request import notify_users

from organization.models import Organization

from json_field import JSONField


class Project(models.Model):
    # Dispatch signals
    branch_new_signal = django.dispatch.Signal(
        providing_args=['new_rev', 'old_rev', 'new_rev_short',
                        'branch', 'pushed_by', 'project'])
    branch_modify_signal = django.dispatch.Signal(
        providing_args=['new_rev', 'old_rev', 'new_rev_short',
                        'branch', 'pushed_by', 'project'])
    branch_delete_signal = django.dispatch.Signal(
        providing_args=['new_rev', 'old_rev', 'new_rev_short',
                        'branch', 'pushed_by', 'project'])
    tag_new_signal = django.dispatch.Signal(
        providing_args=['new_rev', 'old_rev', 'new_rev_short',
                        'tag', 'pushed_by', 'project'])
    tag_modify_signal = django.dispatch.Signal(
        providing_args=['new_rev', 'old_rev', 'new_rev_short',
                        'tag', 'pushed_by', 'project'])
    tag_delete_signal = django.dispatch.Signal(
        providing_args=['new_rev', 'old_rev', 'new_rev_short',
                        'tag', 'pushed_by', 'project'])

    # Fields
    owner = models.ForeignKey(settings.AUTH_USER_MODEL,
                              related_name='projects')
    organization = models.ForeignKey(Organization, null=True)
    fork = models.ForeignKey('Project', related_name='forks', null=True)
    private = models.BooleanField(
        verbose_name=_('Make it a private repository?'), default=False)
    name = models.SlugField(
        verbose_name='Repository Name',
        help_text=_('Enter a valid name consisting of letters, '
                    'numbers, underscores or hyphens.'))
    description = models.CharField(
        verbose_name='Repository Description',
        max_length=255, help_text=_('Enter a short, yet descriptive comment.'))
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    starred_by = models.ManyToManyField(settings.AUTH_USER_MODEL)

    @property
    def git(self):
        if hasattr(self, '_git'):
            return self._git
        self._git = Git(path=self.get_absolute_path())
        return self._git

    @git.setter
    def git(self, value):
        self._git = value

    @transaction.atomic
    def star(self, user):
        self.starred_by.add(user)
        template = 'project/activity-feed/star.html'
        context = {'user': user, 'project': self}
        notify_users(user, template, context)

    @transaction.atomic
    def fork_to(self, user):
        parent = Project.objects.get(pk=self.pk)
        child = Project.objects.get(pk=self.pk)
        child.pk = None
        child.fork = parent
        child.owner = user
        child.save()
        return child

    def unstar(self, user):
        self.starred_by.remove(user)

    def branch_add(self, branch_name):
        template = 'project/activity-feed/branch-add.html'
        context = {'project': self, 'branch': branch_name}
        notify_users(self.starred_by.all(), template, context)

    def branch_remove(self, branch_name):
        template = 'project/activity-feed/branch-remove.html'
        context = {'project': self, 'branch': branch_name}
        notify_users(self.starred_by.all(), template, context)

    def get_absolute_url(self):
        owner = self.owner.username
        if self.organization:
            owner = self.organization.name
        kwds = {'owner': owner, 'project': self.name}
        return reverse('project:view', kwargs=kwds)

    def get_absolute_path(self):
        repo = settings.GIT_REPOSITORY_PATH
        return os.path.join(repo, self.full_name())

    @transaction.atomic
    def save(self, *args, **kwargs):
        self.name = slugify(self.name)
        create_project = self.pk is None
        super(Project, self).save(*args, **kwargs)
        if create_project:
            self.create_project()
        return self

    def create_project(self):
        clone = self.fork.get_absolute_path() if self.fork else None
        project_path = self.get_absolute_path()
        self.git = Git.clone_or_create(path=project_path, clone=clone)

        # Create a new activity stream depending if the project is forked
        template = 'project/activity-feed/created.html'
        context = {'user': self.owner, 'project': self,
                   'organization': self.organization}

        # We either dispatch to the organization or to the owner
        users = (self.owner,)
        if self.organization:
            users = (role.user for role in self.organization.roles)

        if self.fork:
            template = 'project/activity-feed/forked.html'
            context['parent'] = self.fork
            users.append(self.fork.owner)
        notify_users(users, template, context)

    def full_name(self):
        owner = self.owner.username
        if self.organization:
            owner = self.organization.name
        return os.path.join(owner, self.name)

    def notifiable_users(self):
        users = (self.owner,)
        if self.organization:
            users = (role.user for role in self.organization.roles)
        return users

    def post_receive(self, old_rev, new_rev, refname, name, push_user):
        # Determine if we are operating on a branch or tag
        klass = 'branch'
        if 'refs/tags' in refname:
            klass = 'tag'

        # Determine the action on the tag or branch
        action = 'modify'
        empty_old_rev = '00000000'
        if old_rev.startswith(empty_old_rev):
            action = 'new'
        elif new_rev.startswith(empty_old_rev):
            action = 'delete'

        # Create the context
        context = {'old_rev': old_rev,
                   'new_rev': new_rev,
                   'new_rev_short': new_rev[:8],
                   'refname': refname,
                   'pushed_by': push_user,
                   'project': self,
                   klass: name}

        # Dispatch the action
        return self.post_receive_action(klass, action, **context)

    def post_receive_commit(self, commit):
        return Commit.create_from_dulwich(self, commit)

    def post_receive_action(self, klass, action, *args, **kwargs):
        template = 'project/activity-feed/{}-{}.html'.format(klass, action)
        cmd = '{}_{}_signal'.format(klass, action)
        users = self.notifiable_users()
        notify_users(users, template, kwargs)
        getattr(Project, cmd).send(sender=self, **kwargs)

    def __unicode__(self):
        return self.full_name()


class Branch(models.Model):
    branch = models.CharField(max_length=256, db_index=True)
    project = models.ForeignKey(Project, related_name='branches')

    def __unicode__(self):
        return u'{}/{}'.format(self.project, self.branch)


class Commit(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    parents = models.ManyToManyField('Commit', related_name='+')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True)
    author_time = models.DateTimeField()
    author_name = models.CharField(max_length=256)
    author_email = models.EmailField()
    sha1sum = models.CharField(max_length=60, db_index=True)
    commit = models.TextField()
    files_added = JSONField()
    files_modified = JSONField()
    files_deleted = JSONField()
    tree = JSONField()
    branch = models.ForeignKey(Branch, related_name='commits')
    project = models.ForeignKey(Project, related_name='commits')

    def sha1sum_short(self):
        return self.sha1sum[:8]

    @staticmethod
    def create_from_dulwich(project, commit):
        pass

    def __unicode__(self):
        return u'{} @ {}'.format(self.sha1sum_short(), self.project)


class CommitComment(models.Model):
    commit = models.ForeignKey(Commit, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL,
                               related_name='commit_comments')
    comment = models.TextField()

    def __unicode__(self):
        return u'{} -- {}'.format(self.commit.commit, self.comment[:24])


class Tag(models.Model):
    tag = models.CharField(max_length=256, db_index=True)
    project = models.ForeignKey(Project, related_name='tags')
    commit = models.ForeignKey(Commit)

    def __unicode__(self):
        return u'{}/{}'.format(self.project, self.tag)
