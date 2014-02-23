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


SSH_COMMAND = '# Public key for {}\ncommand="./env.bash {}" {} {}\n\n'


logger = logging.getLogger(__name__)


def run(key):
    # Take an initial lock on the authorized_keys
    home = os.environ['HOME']
    llab_keys = os.path.join(home, '.ssh', 'authorized_keys')
    lock = LockFile(llab_keys)
    umask_original = os.umask(0)
    with lock:
        try:
            perms = os.O_RDWR | os.O_APPEND | os.O_EXCL
            mode = stat.S_IRUSR | stat.S_IWUSR
            print(llab_keys)
            with os.fdopen(os.open(llab_keys, perms, mode), 'w+') as f:
                f.write(SSH_COMMAND.format(
                    key.user.username, key.user_id, SSH_DISABLE, key.key))
        finally:
            os.umask(umask_original)
        return True
