import user_streams

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth import models as auth_models
from django.template.loader import render_to_string

from utils.enumeration import make_bitwise_enumeration, BitwiseSet

Permission = make_bitwise_enumeration(
    'Permission', ('download_code', 'fork_project', 'commit', 'read_project',
                   'read_wiki', 'read_issue', 'read_milestone',
                   'read_project_snippet', 'read_team_member',
                   'read_merge_request', 'read_note', 'write_issue',
                   'write_not', 'add_project', 'delete_project', 'add_member',
                   'remove_member'))


class User(AbstractUser):
    """Abstract representation of an entity that can manage projects.

    Users can either be registered people--or organizations.

    """
    owner = models.ForeignKey(User)
    roles = models.ManyToManyField(Role)
    last_event_stream = models.DateTimeField(auto_now_add=True)

    def has_stream_notifications(self):
        return user_streams.get_stream_items(self).filter(seen=False).exists()

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super(User, self).save(*args, **kwargs)
        if is_new:
            template = 'accounts/activity-feed/new-user.html'
            context = {'user': self}
            users = [self]
            content = render_to_string(template, context)
            user_streams.add_stream_item(users, content)


class Group(models.Model):
    name = models.CharField(max_length=255, db_index=True)
    _permissions = models.IntegerField()

    @classmethod
    def builtins(cls):
        names = ('Admin', 'User', 'Test', 'Manager', 'Developer')
        return cls.objects.filter(name__in=names)

    @classmethod
    def get_or_create_from_permission(name, exclude=[]):
        permissions = Permission.permission_as_int(exclude=exclude)
        admin = {'name': name,
                 '_permissions': permissions}
        return cls.objects.get_or_create(**admin)

    @classmethod
    def AdminGroup(cls):
        return cls.get_or_create_from_permission('Admin', exclude=[])

    @classmethod
    def UserGroup(cls):
        exclude = ('add_project', 'delete_project',
                   'add_member', 'remove_member', 'commit')
        return cls.get_or_create_from_permission('User', exclude=exclude)

    @classmethod
    def TestGroup(cls):
        exclude = ('add_project', 'delete_project',
                   'add_member', 'remove_member', 'commit')
        return cls.get_or_create_from_permission('Test', exclude=exclude)

    @classmethod
    def DeveloperGroup(cls):
        exclude = ('add_member', 'remove_member', 'delete_project')
        return cls.get_or_create_from_permission('Manager', exclude=exclude)

    @classmethod
    def ManagerGroup(cls):
        exclude = ('add_member', 'remove_member')
        return cls.get_or_create_from_permission('Manager', exclude=exclude)

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
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='+')
    group = models.ForeignKey(Group, related_name='+')


class Organization(models.Model):
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(User)
    roles = models.ManyToManyField(Role)


auth_models.User = User
