from __future__ import unicode_literals

import os

import dulwich.repo

from functools import partial
from collections import OrderedDict

from dulwich.objects import S_ISGITLINK
from dulwich.patch import is_binary
from dulwich.walk import Walker
from difflib import SequenceMatcher


def sorted_file_folder_tree(tree):
    ordered_tree = OrderedDict()
    modified_tree = ordered_tree

    # Process the intiial node
    for key, value in tree.iteritems():
        modified_tree[key] = value
    modified_tree['tree'] = OrderedDict()

    def process_tree(tr, ot):
        stack, files, folders = [], [], []

        # Iterate through the current tree object
        for name, obj in tr.iteritems():
            if obj['type'] == 'folder':
                folders.append((name, obj))
                stack.append(name)
            else:
                files.append((name, obj))

        # Construct the ordered parameters of the tree
        for name, obj in sorted(folders):
            ot[name] = OrderedDict(obj)
            ot[name]['tree'] = OrderedDict()

        # Construct the ordered parameters of the tree
        for name, obj in sorted(files):
            ot[name] = obj

        # Repeat the process for the new node
        for item in stack:
            ot[item]['type'] = tr[item]['type']
            ot[item]['commit'] = tr[item]['commit']

        for item in stack:
            process_tree(tr[item]['tree'], ot[item]['tree'])

    process_tree(tree['tree'], modified_tree['tree'])
    return ordered_tree


def commit_as_dict(commit):
    start = commit.author.decode('utf-8').rfind('<')
    author_email = commit.author[start + 1:-1]
    start = commit.committer.decode('utf-8').rfind('<')
    committer_email = commit.committer[start + 1:-1]

    return {'author': commit.author,
            'author_email': author_email,
            'author_time': commit.author_time,
            'author_timezone': commit.author_timezone,
            'commit_time': commit.commit_time,
            'commit_timezone': commit.commit_timezone,
            'committer': commit.committer,
            'committer_email': committer_email,
            'message': commit.message.decode('utf-8').split('\n')[0][:50],
            'sha': commit.sha().hexdigest()}


def unified_diff(a, b, n=3):
    diff, added, deleted = [], 0, 0
    line_offset = 0
    for g in SequenceMatcher(None, a, b).get_grouped_opcodes(n):
        i1, i2, j1, j2 = g[0][1], g[-1][2], g[0][3], g[-1][4]
        diff.append(('', 'diff', ''))
        for tag, i1, i2, j1, j2 in g:
            if tag == 'equal':
                for i, line in enumerate(a[i1:i2], start=i1):
                    diff.append((i + line_offset, 'equal', line))
                continue
            if tag == 'replace' or tag == 'delete':
                for i, line in enumerate(a[i1:i2], start=i1):
                    if not line[-1] == u'\n':
                        pass
                    if tag == 'delete':
                        line_offset -= 1
                    entry = (i, 'delete', line)
                    diff.append(entry)
                    deleted += 1
            if tag == 'replace' or tag == 'insert':
                for i, line in enumerate(b[j1:j2], start=j1):
                    if not line[-1] == u'\n':
                        pass
                    if tag == 'insert':
                        line_offset += 1
                    entry = (i, 'insert', line)
                    diff.append(entry)
                    added += 1
    return diff, added, deleted


class Git(object):
    """A wrapper around dulwich which is a git-protocol Python layer.

    These methods simplify the more common commands with llab.

    """
    def __init__(self, path=None, repo=None):
        if repo or path:
            self.repo = repo if repo else dulwich.repo.Repo(path)
        else:
            raise os.error('path or repo was not specified or found')

    def commit_changes(self, message):
        return self.repo.commit(message=message)

    def head(self):
        try:
            return self.repo.head()
        except KeyError:
            return next(self.repo.get_refs().itervalues())

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

        def update_refs(refs, branch):
            branch = 'refs/heads/' + branch
            refs[branch] = repo[branch]

        update_refs_wrap = partial(update_refs, branch=branch)
        return client.send_pack(path, update_refs_wrap, pack_contents)

    def lstree(self, sha=None):
        sha = sha or self.head()
        repo = self.repo
        t1 = repo[sha].tree

        tree = {'commit': None,
                'type': 'folder',
                'tree': {}}

        for entry in self.repo.object_store.iter_tree_contents(t1):
            path = entry.path
            blob = entry.sha
            dirs, filename = os.path.split(path)
            dirs_split = dirs.split('/') if len(dirs) else []

            entry = {'commit': None,
                     'blob': blob,
                     'type': 'file',
                     'path': path}

            # Construct a top-level descriptor
            if not dirs:
                tree['tree'][filename] = entry
                continue

            # Construct a tree with all the parts
            rel_tree = tree['tree']
            rel_part = []
            for part in dirs_split:
                rel_part.append(part)
                if not rel_tree.get(part):
                    rel_tree[part] = {'commit': None,
                                      'type': 'folder',
                                      'path': '/'.join(rel_part),
                                      'tree': {}}
                rel_tree = rel_tree[part]['tree']
            rel_tree[filename] = entry

        return sorted_file_folder_tree(tree)

    def commit_for_files(self, paths, sha=None):
        r = self.repo
        sha = sha or self.head()
        paths = list(paths)
        seen = set()
        files = set(paths)
        path_stack = len(paths)

        for walker in r.get_walker(paths=paths, include=[sha]):
            for changes in walker.changes():
                if not isinstance(changes, list):
                    changes = [changes]
                for change in changes:
                    path = change.old.path or change.new.path
                    if path not in seen and path in files:
                        seen.add(path)
                        path_stack -= 1
                        yield path, commit_as_dict(walker.commit)
                    if not path_stack:
                        break
                if not path_stack:
                    break
            if not path_stack:
                break

    def commit_for_file(self, filename, sha=None):
        return self.commit_for_files([filename], sha)

    def commit_for_directory(self, directory, sha=None):
        assert(directory.endswith('/'))

        r = self.repo
        sha = sha or self.head()

        def paths():
            t1 = r[sha].tree
            for entry in self.repo.object_store.iter_tree_contents(t1):
                path = entry.path
                directory2, filename = os.path.split(path)
                if directory == directory2:
                    yield path

        return self.commit_for_files(paths(), sha)

    def branches(self):
        refs = self.repo.refs.as_dict()
        rkey = 'refs/heads/'
        return {k: v for k, v in refs.iteritems() if k.startswith(rkey)}

    def commits(self, sha_only=False, branch='master'):
        refs = self.repo.refs.as_dict()
        ref = refs.get(branch, refs.get('refs/heads/' + branch, None))
        if not ref:
            raise KeyError(branch)
        for walker in Walker(self.repo, include=[ref]):
            commit = walker.commit
            if sha_only:
                yield commit.sha().hexdigest()
            else:
                yield commit

    def commit_count(self, branch):
        return len(list(self.commits(branch=branch)))

    def last_commit(self, sha_only=False, branch='master'):
        return next(self.commits(sha_only=sha_only, branch=branch))

    def difflist(self, old_rev, new_rev):
        r = self.repo
        store = r.object_store

        try:
            old_tree = r[old_rev].tree
        except KeyError:
            old_tree = self.head()

        new_tree = r[new_rev].tree
        changes = store.tree_changes(old_tree, new_tree)

        def shortid(hexsha):
            if hexsha is None:
                return '0' * 7
            return hexsha[:7]

        def content(mode, hexsha):
            if hexsha is None:
                return ''
            elif S_ISGITLINK(mode):
                return 'Submodule commit {}\n'.format(hexsha)
            else:
                return store[hexsha].data

        def lines(content):
            if not content:
                return []
            else:
                return content.splitlines(True)

        tree = {'stats': {'files_added': 0,
                          'files_deleted': 0,
                          'lines_added': 0,
                          'lines_deleted': 0,
                          'lines_added_ratio': 0,
                          'lines_deleted_ratio': 0},
                'changes': []}

        for path, mode, sha in changes:
            old_path, old_mode, old_sha = path[1], mode[1], sha[1]
            new_path, new_mode, new_sha = path[0], mode[0], sha[0]
            file_added = False
            file_deleted = False

            if not old_path:
                old_path = new_path
                file_added = True

            if not new_path:
                new_path = old_path
                file_deleted = True

            # Construct our object entry
            entry = {'old_path': old_path,
                     'new_path': new_path,
                     'old_mode': old_mode,
                     'new_mode': new_mode,
                     'file_added': file_added,
                     'file_deleted': file_deleted,
                     'lines_added': 0,
                     'lines_deleted': 0,
                     'diff': []}

            # Fetch all of the content
            old_content = content(old_mode, old_sha)
            new_content = content(new_mode, new_sha)

            if is_binary(old_content) or is_binary(new_content):
                msg = 'Binary files {} and {} are different'
                entry['diff'] = msg.format(old_path, new_path)
                entry['lines_added'] = 0
                entry['lines_deleted'] = 0
                entry['lines_added_ratio'] = 0
                entry['lines_deleted_ratio'] = 0
            else:
                # Diff the file for changes
                new_lines = lines(new_content)
                old_lines = lines(old_content)
                diff, added, deleted = unified_diff(old_lines, new_lines)
                entry['diff'] = diff
                entry['lines_added'] += added
                entry['lines_deleted'] += deleted
                total = float(entry['lines_added'] + entry['lines_deleted'])
                if total > 0:
                    lines_added = entry['lines_added'] * 100.0
                    lines_deleted = entry['lines_deleted'] * 100.0
                    entry['lines_added_ratio'] = lines_added / total
                    entry['lines_deleted_ratio'] = lines_deleted / total

            # Aggregate statistics
            tree['stats']['lines_added'] += entry['lines_added']
            tree['stats']['lines_deleted'] += entry['lines_deleted']
            tree['changes'].append(entry)

        return tree

    def commit(self, old_rev):
        return self.repo[old_rev]

    @classmethod
    def clone_or_create(cls, path, clone=None):
        """clone_or_create -> Git.

        Either create a bare repository provided by the path, or fork from
        the clone path as a bare repository.

        """
        path = os.path.abspath(path)
        if not os.path.exists(path):
            os.makedirs(path)

        # Clone the data and the copy the hooks
        if not clone:
            inst = cls.from_repo(dulwich.repo.Repo.init_bare(path))
        else:
            clone_repo = dulwich.repo.Repo(clone)
            inst = cls.from_repo(clone_repo.clone(target_path=path, bare=True))
        inst.refresh_hooks()
        return inst

    def refresh_hooks(self):
        import shutil
        path = self.repo.path
        repo_hooks = os.path.join(path, 'hooks')
        module_dir = os.path.dirname(os.path.abspath(__file__))
        hooks = os.path.join(module_dir, 'hooks')
        hooks_added = []
        for fn in os.listdir(hooks):
            a = os.path.join(hooks, fn)
            b = os.path.join(repo_hooks, fn)
            if not os.path.isfile(a):
                continue
            hooks_added.append(b)
            shutil.copy2(a, b)
        return hooks

    def fetch_blob(self, sha1sum):
        return self.repo[sha1sum].data

    @classmethod
    def from_repo(cls, repo):
        """from_repo -> Git.

        Creates a new Git instance based on the dulwich repo.

        """
        return Git(repo=repo)

    def archive(self, commit, compress='bzip2'):
        import subprocess
        pipe = subprocess.PIPE
        git_dir = self.repo.path
        work_tree = self.repo.path

        compress_methods = {'bzip2': ('bzip2',),
                            'gzip': ('gzip', '-9')}
        pipe_cmd = compress_methods.get(compress, 'bzip2')

        # HACK(justinvh): Unless I am blind Dulwich does not support
        #                 archiving repositories, so we use subprocess
        #                 to pipe and return the results.
        cmd = ('git', '--git-dir={}'.format(git_dir),
               '--work-tree={}'.format(work_tree), 'archive', commit)
        ps = subprocess.Popen(cmd, stdout=pipe)
        output = subprocess.check_output(pipe_cmd, stdin=ps.stdout)
        ps.wait()
        return output
