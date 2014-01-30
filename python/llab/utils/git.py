import os
import dulwich.repo


class Git(object):
    """A wrapper around dulwich which is a git-protocol Python layer.

    These methods simplify the more common commands with llab.

    """
    def __init__(self, path=None, repo=None):
        if repo or path:
            self.repo = repo if repo else dulwich.repo.Repo(path)
        else:
            raise os.error('path or repo was not specified or found')

    @classmethod
    def clone_or_create(cls, path, clone=None):
        """clone_or_create -> Git.

        Either create a bare repository provided by the path, or fork from
        the clone path as a bare repository.

        """
        if not os.path.exists(path):
            os.makedirs(path)
        if not clone:
            return cls.from_repo(dulwich.repo.Repo.init_bare(path))
        clone_repo = dulwich.repo.Repo(clone)
        return cls.from_repo(clone_repo.clone(target_path=path, bare=True))

    @classmethod
    def from_repo(cls, repo):
        """from_repo -> Git.

        Creates a new Git instance based on the dulwich repo.

        """
        return Git(repo=repo)
