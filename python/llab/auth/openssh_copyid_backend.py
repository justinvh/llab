import os
import stat
import time
import logging
import random

from lockfile import LockFile


SSH_DISABLE = ('no-port-forwarding,'
               'no-x11-forwarding,'
               'no-pty,'
               'no-agent-forwarding')


SSH_COMMAND = '# {}-{}\ncommand="./env.bash {}",{} {}\n\n'


home = os.environ['HOME']
llab_keys = os.path.join(home, '.ssh', 'authorized_keys')
lock = LockFile(llab_keys)
logger = logging.getLogger(__name__)


def delete(user_key):
    with lock:
        if not os.path.exists(llab_keys):
            return False

        key_name = user_key.name
        user_id = user_key.user_id

        found = False
        keys = open(llab_keys).read().split('\n')
        needle = '# {}-{}'.format(user_id, key_name)
        for i, key in enumerate(keys):
            if key.startswith(needle):
                keys = keys[:i] + keys[i + 3:]
                found = True
                break

        if not found:
            return False

        keys = '\n'.join(keys)
        umask_original = os.umask(0)
        try:
            with open(llab_keys, 'wt'):
                os.chmod(llab_keys, 0o600)
            perms = os.O_RDWR | os.O_APPEND | os.O_EXCL
            mode = stat.S_IRUSR | stat.S_IWUSR
            with os.fdopen(os.open(llab_keys, perms, mode), 'w') as f:
                f.write(keys)
        finally:
            os.umask(umask_original)
        return True


def run(key):
    # Take an initial lock on the authorized_keys
    umask_original = os.umask(0)
    with lock:
        try:
            if not os.path.exists(llab_keys):
                with open(llab_keys, 'wt'):
                    os.chmod(llab_keys, 0o600)
            perms = os.O_RDWR | os.O_APPEND | os.O_EXCL
            mode = stat.S_IRUSR | stat.S_IWUSR
            with os.fdopen(os.open(llab_keys, perms, mode), 'w+') as f:
                f.write(SSH_COMMAND.format(
                    key.user_id, key.name, key.user_id, SSH_DISABLE, key.key))
        finally:
            os.umask(umask_original)
        return True
