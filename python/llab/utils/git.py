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

    def commit(self, message):
        return self.repo.commit(message=message)

    def add(self, file_or_files):
        files = file_or_files
        if not isinstance(file_or_files, (list, tuple)):
            files = [file_or_files]
        return self.repo.add(paths=files)

    def push(self, remote, branch):
        from dulwich.client import get_transport_and_path
        repo = self.repo
        client, path = get_transport_and_path(remote)
        pack_contents = repo.object_store.generate_pack_contents
        def update_refs(refs):
            branch = 'refs/heads/' + branch
            refs[branch] = repo[branch]
        return client.send_pack(path, update_refs, pack_contents)

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
