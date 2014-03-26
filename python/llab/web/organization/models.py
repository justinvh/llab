from django.db import models
from django.conf import settings
from django.core.urlresolvers import reverse

from llab.utils.enumeration import make_bitwise_enumeration, BitwiseSet

Permission = make_bitwise_enumeration(
    'Permission', (('download_code', 'Download code'),
                   ('fork_project', 'Fork projects'),
                   ('commit', 'Commit to projects'),
                   ('read_project', 'View projects'),
                   ('read_wiki', 'Read Wikis belonging'),
                   ('read_issue', 'View issues'),
                   ('read_milestone', 'View milestones'),
                   ('read_project_snippet', 'View project snippets'),
                   ('read_team_member', 'View team members'),
                   ('read_merge_request', 'View merge requests'),
                   ('read_note', 'Read project notes'),
                   ('write_issue', 'Create issues'),
                   ('write_not', 'Placeholder'),
                   ('add_project', 'Create projects'),
                   ('delete_project', 'Delete projects'),
                   ('add_member', 'Add members'),
                   ('remove_member', 'Remove members')))


class Group(models.Model):
    name = models.CharField(max_length=255, db_index=True)
    organization = models.ForeignKey('Organization', related_name='groups')
    _permissions = models.IntegerField()

    def __unicode__(self):
        return self.name

    @classmethod
    def builtins(cls, organization):
        names = ('Admin', 'User', 'Test', 'Manager', 'Developer')
        return cls.objects.filter(name__in=names, organization=organization)

    @classmethod
    def create_builtins(cls, organization):
        groups = (cls.AdminGroup, cls.UserGroup, cls.TestGroup,
                  cls.DeveloperGroup, cls.ManagerGroup)
        for get_or_create_group in groups:
            get_or_create_group(organization)
        return cls.builtins(organization)

    @classmethod
    def get_or_create_from_permission(cls, name, organization, exclude=[]):
        permissions = Permission.permission_as_int(exclude=exclude)
        admin = {'name': name,
                 'organization': organization,
                 '_permissions': permissions}
        return cls.objects.get_or_create(**admin)

    @classmethod
    def AdminGroup(cls, org):
        return cls.get_or_create_from_permission('Admin', org, exclude=[])

    @classmethod
    def UserGroup(cls, org):
        exclude = ('add_project', 'delete_project',
                   'add_member', 'remove_member', 'commit')
        return cls.get_or_create_from_permission('User', org, exclude=exclude)

    @classmethod
    def TestGroup(cls, org):
        exclude = ('add_project', 'delete_project',
                   'add_member', 'remove_member', 'commit')
        return cls.get_or_create_from_permission('Test', org, exclude=exclude)

    @classmethod
    def DeveloperGroup(cls, org):
        exc = ('add_member', 'remove_member', 'delete_project')
        return cls.get_or_create_from_permission('Developer', org, exclude=exc)

    @classmethod
    def ManagerGroup(cls, org):
        exc = ('add_member', 'remove_member')
        return cls.get_or_create_from_permission('Manager', org, exclude=exc)

    @property
    def permissions(self):
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


class Organization(models.Model):
    name = models.SlugField(
        unique=True, verbose_name='Organization Name',
        help_text=('Enter a valid name consisting of letters, '
                   'numbers, underscores or hyphens.'))
    owner = models.ForeignKey(settings.AUTH_USER_MODEL)

    def get_role_management_absolute_url(self):
        kwds = {'organization': self.name}
        return reverse('organization:roles', kwargs=kwds)


class Role(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='+')
    group = models.ForeignKey(Group, related_name='+')
    organization = models.ForeignKey(Organization, related_name='roles')

