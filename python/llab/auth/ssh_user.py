import os

from project.models import Project
from account.models import User


class AuthenticationError(Exception):
    """The user failed to authenticate"""


class BadUserError(AuthenticationError):
    """The user is invalid"""


class BadProjectError(AuthenticationError):
    """The project is invalid"""


def authenticate(user_id, project_path):
    try:
        # Verify that this project is managed and available
        path_split = project_path.split(os.sep)
        if len(path_split) != 2:
            raise BadProjectError('An invalid project was specified.')

        owner, project_name = path_split
        project = Project.objects.get(owner__username=owner, name=project_name)
        user = User.objects.get(pk=user_id)

        # Easy check, owners can always commit
        if project.owner == user:
            return project, user

        # If they are part of the organization and have commit access
        if project.organization and project.organization.user_can_commit(user):
            return project, user

        # Otherwise the user can not commit to this project.
        m = '[DENIED] {} does not have permissions to commit to "{}".'
        raise AuthenticationError(m.format(user.username, project.full_name()))

    except Project.DoesNotExist:
        raise BadProjectError('[DENIED] An invalid project was specified.')

    except User.DoesNotExist:
        raise BadUserError('[DENIED] You are not registered.')
