import os
import sys
import datetime
import socket
import mimetypes
import logging
import copy
import json

import pytz

import django.dispatch

from collections import OrderedDict, defaultdict

from django.db import models, transaction
from django.core.urlresolvers import reverse
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext_lazy as _

from django.conf import settings
from llab.utils.git import Git, sorted_file_folder_tree
from llab.utils.request import notify_users

from organization.models import Organization

from json_field import JSONField


logger = logging.getLogger(__name__)


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

    # Some dynamic stats
    contributors = JSONField(decoder_kwargs={'object_pairs_hook': OrderedDict})

    @property
    def git(self):
        if hasattr(self, '_git'):
            return self._git
        self._git = Git(path=self.get_absolute_path())
        return self._git

    @git.setter
    def git(self, value):
        self._git = value

    def refresh_contributors(self):
        stats = defaultdict(int)
        email_names = defaultdict(set)
        name_emails = defaultdict(set)
        seen_names = set()
        total_commits = 0
        min_commit_time, max_commit_time = (sys.maxint, 0)

        # Populate the commit table
        commits = {}
        for branch in self.branches.all():
            for commit in self.git.commits(branch=branch.name):
                commits[commit.sha().hexdigest()] = commit

        for commit in commits.itervalues():
            start = commit.author.decode('utf-8').rfind('<')
            email = commit.author[start + 1:-1]
            name = commit.author[:start]
            if name in seen_names:
                email = iter(name_emails[name]).next()
            stats[email] += 1
            email_names[email].add(name)
            name_emails[name].add(email)
            seen_names.add(name)
            total_commits += 1
            if commit.author_time > max_commit_time:
                max_commit_time = commit.author_time
            elif commit.author_time < min_commit_time:
                min_commit_time = commit.author_time

        # Try to normalize the data
        normalized = defaultdict(int)
        normalized_aliases_email = defaultdict(set)
        normalized_aliases_name = defaultdict(set)
        for email, value in stats.iteritems():
            normalized_aliases_name[email] = email_names[email]
            normalized[email] += value
            if len(email_names[email]) == 1:
                continue
            for name in email_names[email]:
                normalized_aliases_name[email].add(name)
                for sec_email in name_emails[email]:
                    normalized[email] += stats[sec_email]
                    normalized_aliases_email[email].add(sec_email)
                    normalized[email] += stats[sec_email]

        # Figure out the ratios
        SECONDS_PER_DAY = 86400.0
        days = (max_commit_time - min_commit_time) / SECONDS_PER_DAY
        for key, value in normalized.iteritems():
            ratio = (value / float(total_commits)) * 100.0
            per_day = round(value / days, 2)

            names = normalized_aliases_name[key]
            emails = normalized_aliases_email[key]

            has_multiple_emails = len(emails) > 1
            has_multiple_names = len(names) > 1

            primary_email = key
            primary_name = iter(names).next()

            stats[key] = {'ratio': round(ratio, 3),
                          'count': value,
                          'per_day': per_day,
                          'has_multiple_emails': has_multiple_emails,
                          'has_multiple_names': has_multiple_names,
                          'primary_name': primary_name,
                          'primary_email': primary_email,
                          'emails': list(emails),
                          'names': list(names)}

        sort = sorted(stats.items(), key=lambda i: -i[1]['ratio'])
        self.contributors = OrderedDict(sort)
        self.save()
        return self.contributors

    def is_admin(self, user):
        if user == self.owner:
            return True
        if self.organization and self.organization.is_admin(user):
            return True
        return False

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
        users = self.notifiable_users()
        notify_users(users, template, context)

    def branch_delete(self, branch_name):
        try:
            branch = self.branches.get(name=branch_name)
            branch.delete()
        except Branch.DoesNotExist:
            pass
        template = 'project/activity-feed/branch-delete.html'
        context = {'project': self, 'branch': branch_name}
        users = self.notifiable_users()
        notify_users(users, template, context)

    def tag_add(self, tag_name):
        template = 'project/activity-feed/tag-add.html'
        context = {'project': self, 'tag': tag_name}
        users = self.notifiable_users()
        notify_users(users, template, context)

    def tag_delete(self, tag_name):
        try:
            tag = self.tags.get(name=tag_name)
            tag.delete()
        except Tag.DoesNotExist:
            pass
        template = 'project/activity-feed/tag-delete.html'
        context = {'project': self, 'tag': tag_name}
        users = self.notifiable_users()
        notify_users(users, template, context)

    def get_absolute_url(self):
        owner = self.owner.username
        if self.organization:
            owner = self.organization.name
        kwds = {'owner': owner, 'project': self.name}
        return reverse('project:view', kwargs=kwds)

    def get_absolute_commit_list_url(self):
        owner = self.owner.username
        if self.organization:
            owner = self.organization.name
        branch = self.branches.earliest('id')
        kwds = {'owner': owner, 'project': self.name, 'branch': branch.name}
        return reverse('project:commit:list', kwargs=kwds)

    def get_absolute_branch_list_url(self):
        owner = self.owner.username
        if self.organization:
            owner = self.organization.name
        kwds = {'owner': owner, 'project': self.name}
        return reverse('project:branches', kwargs=kwds)

    def get_absolute_tag_list_url(self):
        owner = self.owner.username
        if self.organization:
            owner = self.organization.name
        kwds = {'owner': owner, 'project': self.name}
        return reverse('project:tags', kwargs=kwds)

    def get_contributors_url(self):
        owner = self.owner.username
        if self.organization:
            owner = self.organization.name
        kwds = {'owner': owner, 'project': self.name}
        return reverse('project:contributors', kwargs=kwds)

    def get_absolute_path(self):
        repo = settings.GIT_REPOSITORY_PATH
        return os.path.join(repo, self.full_name())

    def get_private_clone_path(self):
        hostname = socket.gethostname()
        username = os.environ.get('USER', 'git')
        return u'{}@{}:{}'.format(username, hostname, self.full_name())

    def get_public_clone_path(self):
        hostname = socket.gethostname()
        return u'http://{}/{}'.format(hostname, self.full_name())

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

    def latest_commit(self):
        return self.commits.latest('created')

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
                   'new_rev_short': new_rev[:7],
                   'refname': refname,
                   'pushed_by': push_user,
                   'project': self,
                   klass: name}

        # Dispatch the action
        dispatch = self.post_receive_action(klass, action, **context)

        # Refresh dynamic attributes
        self.refresh_contributors()

        return dispatch

    def post_receive_tag(self, action, old_rev, tag_rev, refname):
        if action == 'delete':
            self.tag_delete(refname)
            return

        # Fetch the actual revision from the object
        obj = self.git.repo[tag_rev]
        if hasattr(obj, 'object'):
            obj, new_rev = obj.object
        else:
            new_rev = obj.id

        project = self
        commit = Commit.create_from_sha(project, new_rev)

        try:
            tags = Tag.objects.filter(project=project, name=refname)
            tag = tags.latest('id')
        except Tag.DoesNotExist:
            tag = Tag(project=project, name=refname, ref=commit)
            tag.save()

    def post_receive_commit(self, action, old_rev, new_rev, refname):
        if action == 'delete':
            self.branch_delete(refname)
            return

        project = self
        commit = Commit.create_from_sha(project, new_rev)

        try:
            branches = Branch.objects.filter(project=project, name=refname)
            branch = branches.latest('id')
        except Branch.DoesNotExist:
            branch = Branch(project=project, name=refname, ref=commit)
            branch.save()
        branch.update_refs_and_stats()

    def post_receive_action(self, klass, action, *args, **kwargs):
        refname = kwargs['refname']
        old_rev, new_rev = kwargs['old_rev'], kwargs['new_rev']

        if klass == 'branch':
            self.post_receive_commit(action, old_rev, new_rev, refname)
        elif klass == 'tag':
            self.post_receive_tag(action, old_rev, new_rev, refname)

        template = 'project/activity-feed/{}-{}.html'.format(klass, action)
        cmd = '{}_{}_signal'.format(klass, action)
        users = self.notifiable_users()
        notify_users(users, template, kwargs)
        getattr(Project, cmd).send(sender=self, **kwargs)

    def __unicode__(self):
        return self.full_name()


class Commit(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    commit_time = models.DateTimeField()
    sha1sum = models.CharField(max_length=60, db_index=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, null=True,
                               related_name='author_for_commits')
    author_email = models.EmailField()
    author_name = models.CharField(max_length=256)
    author_time = models.DateTimeField()
    committer = models.ForeignKey(settings.AUTH_USER_MODEL, null=True,
                                  related_name='committed_for_commits')
    committer_name = models.CharField(max_length=256)
    committer_email = models.EmailField()
    message = models.TextField()

    # A list of parents
    parents = JSONField()

    # The diffs of the commit
    _diff = JSONField()

    # The current tree as of this commit
    _tree = JSONField(decoder_kwargs={'object_pairs_hook': OrderedDict})

    # The related branch and project for this commit
    project = models.ForeignKey(Project, related_name='commits')

    @property
    def tree(self):
        if not self._tree:
            self.refresh_tree()
            self.save()
        return self._tree

    @tree.setter
    def tree(self, value):
        self._tree = value

    def refresh_tree(self):
        self._tree = self.project.git.lstree(sha=self.sha1sum)

    def refresh_diff(self):
        commit = self.project.git.commit(self.sha1sum)
        diffs = []
        for parent in commit.parents:
            diff = self.project.git.difflist(self.sha1sum, parent)
            diffs.append(diff)
        self._diff = diffs

    @property
    def diff(self):
        if not self._diff:
            self.refresh_diff()
            self.save()
        return self._diff

    def short_message(self):
        return self.message.split('\n')[0]

    def message_header(self):
        return self.short_message()

    def message_body(self):
        items = self.message.split('\n')[1:]
        items_len = len(items)
        for i, item in enumerate(items, start=1):
            if not item.strip():
                continue
            if i == items_len:
                yield item
            else:
                yield item + '\n'

    def short_sha1sum(self):
        return self.sha1sum[:7]

    def revtree(self, folder, as_json=False):
        """Compute or retrieve the revision tree for a given folder path.

        The revision tree includes the commit details for a given path.
        This method will attempt to find the path and then compute the
        revision tree for that level.

        """
        original_tree = self.tree
        original_dirtree = original_tree
        parent_tree = original_tree

        original_tree = original_tree['tree']

        # There is a special case where you are looking at the top-level
        assert(not folder.endswith('/'))
        folders = folder.split('/')
        if len(folders) == 1 and folders[0] == "":
            folders = []

        # We can try "repairing" the tree early on so we do less work
        try:
            rhs = Commit.objects.filter(commit_time__gt=self.commit_time)
            rhs = rhs.earliest('commit_time')
            rhs = rhs.tree
        except Commit.DoesNotExist:
            rhs = [None]

        try:
            lhs = Commit.objects.filter(commit_time__lt=self.commit_time)
            lhs = lhs.latest('commit_time')
            lhs = lhs.tree
        except Commit.DoesNotExist:
            lhs = [None]

        # Iterate through the trees and try to determine good data
        for directory in folders:
            if directory not in original_tree:
                raise KeyError('{} for {}'.format(directory, folder))
            original_dirtree = original_tree[directory]
            original_tree = original_tree[directory]['tree']
            rhs = rhs[directory]['tree'] if directory in rhs else [None]
            lhs = lhs[directory]['tree'] if directory in lhs else [None]

        # If we have the original tree and the commit, then no work needed
        if original_dirtree['commit']:
            dirtree = copy.deepcopy(original_dirtree)
            if as_json:
                return json.dumps(dirtree)
            return sorted_file_folder_tree(dirtree)

        # We need nodes on both sides of the tree to determine if we can
        # skip the current filepath. This ensures that the current tree
        # did not have tree modifications
        def paths():
            for path, entry in original_tree.iteritems():
                if entry['type'] == 'file':
                    if rhs and lhs and path in rhs and path in lhs:
                        if lhs[path]['blob'] == rhs[path]['blob']:
                            continue
                    yield entry['path']
                """
                elif entry['type'] == 'folder':
                    slhs = lhs[path]['tree'] if path in lhs else None
                    srhs = rhs[path]['tree'] if path in rhs else None
                    subtrees = [entry['tree']]
                    break_subtrees = False
                    while subtrees:
                        subtree = subtrees.pop()
                        for subpath, subentry in subtree.iteritems():
                            if slhs and srhs and path in slhs and path in srhs:
                                if slhs[path]['blob'] == srhs[path]['blob']:
                                    continue
                            if entry['type'] == 'folder':
                                subtrees.append(entry['tree'])
                            else:
                                break_subtrees = True
                                yield entry['path']
                        if break_subtrees:
                            break
                """

        # Repair the nodes that we don't have
        git = self.project.git
        sha1sum = self.sha1sum
        commits = git.commit_for_files(sha=sha1sum, paths=paths())
        original_dirtree['commit'] = True
        for path, commit in commits:
            directory, filename = os.path.split(path)
            directory = directory[len(folder):]
            if filename in original_tree:
                original_tree[filename]['commit'] = commit
                continue
            subtree = original_tree
            for subdir in directory.split(os.sep):
                subtree = subtree[subdir]
                subtree['commit'] = commit
                subtree = subtree['tree']
            subtree[filename]['commit'] = commit
        self.tree = parent_tree
        self.save()

        # Copy the tree and return the sorted variant
        dirtree = copy.deepcopy(original_dirtree)
        if as_json:
            return json.dumps(dirtree)
        return dirtree

    def fetch_blob(self, path):
        tree = self.tree['tree']
        directories, filename = os.path.split(path)
        directories = directories.split('/') if len(directories) else []
        for item in directories:
            if item not in tree:
                raise KeyError('{} for {}'.format(item, path))
            tree = tree[item]['tree']
        content = self.project.git.fetch_blob(tree[filename]['blob'])
        content_type, _ = mimetypes.guess_type(filename)
        content_type = content_type or 'text/plain'
        return content, content_type

    @staticmethod
    def get_or_create_from_sha(project, rev):
        try:
            commit = Commit.objects.filter(project=project, sha1sum=rev)
            return commit.latest('id')
        except Commit.DoesNotExist:
            try:
                project.git.commit(rev)
                return Commit.create_from_sha(project, rev)
            except KeyError as e:
                raise Commit.DoesNotExist(e)

    @staticmethod
    def create_from_sha(project, new_rev, create=True):
        from account.models import User
        new_rev_commit = project.git.commit(new_rev)

        # Extract the project tree and diffs
        parents = [p for p in new_rev_commit.parents]

        # Extract formatted author details
        new_author = new_rev_commit.author
        author_info = User.from_commit(new_author, project)
        author, author_name, author_email = author_info

        # Extract formatted committer details
        new_committer = new_rev_commit.committer
        committer_info = User.from_commit(new_committer, project)
        committer, committer_name, committer_email = committer_info

        fts = datetime.datetime.utcfromtimestamp
        utc = pytz.timezone('UTC')

        author_time = new_rev_commit.author_time
        author_time = utc.localize(fts(author_time))

        commit_time = new_rev_commit.commit_time
        commit_time = utc.localize(fts(commit_time))

        # The actual Commit object is fairly heavy
        c = Commit(commit_time=commit_time,
                   sha1sum=new_rev_commit.sha().hexdigest(),
                   author=author,
                   author_name=author_name,
                   author_email=author_email,
                   author_time=author_time,
                   committer=committer,
                   committer_name=committer_name,
                   committer_email=committer_email,
                   message=new_rev_commit.message,
                   diff=[],
                   tree=[],
                   parents=parents,
                   project=project)

        if create:
            c.save()
        return c

    def get_absolute_url(self):
        project = self.project
        owner = project.owner
        if project.organization:
            owner = project.organization.name
        kwds = {'owner': owner, 'project': project.name,
                'commit': self.sha1sum}
        return reverse('project:commit:view', kwargs=kwds)

    def get_absolute_tree_url(self):
        project = self.project
        owner = project.owner
        if project.organization:
            owner = project.organization.name
        kwds = {'owner': owner, 'project': project.name,
                'commit': self.sha1sum}
        return reverse('project:tree_commit_pathless', kwargs=kwds)

    def __unicode__(self):
        return u'{} @ {}'.format(self.short_sha1sum(), self.project)


class CommitComment(models.Model):
    commit = models.ForeignKey(Commit, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL,
                               related_name='commit_comments')
    comment = models.TextField()

    def __unicode__(self):
        return u'{} -- {}'.format(self.commit.commit, self.comment[:24])


class Branch(models.Model):
    name = models.CharField(max_length=256, db_index=True)
    project = models.ForeignKey(Project, related_name='branches')
    ref = models.ForeignKey(Commit, related_name='branches')
    commit_count = models.IntegerField(default=0)

    def update_refs_and_stats(self):
        git = self.project.git
        self.commit_count = git.commit_count(self.name)
        last_commit = git.last_commit(branch=self.name, sha_only=True)
        if self.ref.sha1sum != last_commit:
            ref = Commit.create_from_sha(self.project, last_commit)
            self.ref = ref
        self.save()

    def get_absolute_url(self):
        project = self.project
        owner = project.owner
        if project.organization:
            owner = project.organization.name
        kwds = {'owner': owner, 'project': project.name,
                'commit': self.name}
        return reverse('project:tree_pathless', kwargs=kwds)

    def short_name(self):
        return self.name.split('/')[-1]

    def __unicode__(self):
        return u'{}/{}'.format(self.project, self.name)


class Tag(models.Model):
    name = models.CharField(max_length=256, db_index=True)
    project = models.ForeignKey(Project, related_name='tags')
    created = models.DateTimeField(auto_now_add=True)
    ref = models.ForeignKey(Commit, related_name='tags')

    def short_name(self):
        return self.name.split('/')[-1]

    def download_filename(self, fmt='bzip2'):
        fmts = {'bzip2': '.tar.bz2',
                'gzip': '.tar.gz'}
        fmt = fmts.get(fmt, 'bzip2')
        name = '{}-{}{}'
        return name.format(self.project.name, self.short_name(), fmt)

    def get_absolute_download_url(self):
        project = self.project
        owner = project.owner
        if project.organization:
            owner = project.organization.name
        name = self.name
        kwds = {'owner': owner, 'project': project.name, 'tag': name}
        return reverse('project:download', kwargs=kwds)

    class Meta:
        ordering = ('-id',)

    def __unicode__(self):
        return u'{}/{}'.format(self.project, self.name)


class Requirement(models.Model):
    project = models.ManyToManyField(Project, related_name='requirements')
    belongs_to = models.ManyToManyField(
        'self', related_name='contains', null=True, blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL,
                              related_name='requirements')
    organization = models.ForeignKey(Organization, null=True)
    name = models.SlugField(
        verbose_name='Requirement Name',
        help_text=_('Enter a valid name consisting of letters, '
                    'numbers, underscores or hyphens.'))
    description = models.TextField(
        verbose_name='Requirement Description',
        help_text=_('Describe this requirement.'))
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    starred_by = models.ManyToManyField(settings.AUTH_USER_MODEL)
    fulfilled_by = models.ManyToManyField(
        Commit, related_name='requirements', blank=True)
    fulfilled = models.BooleanField(default=False)
