import user_streams

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth import models as auth_models
from django.template.loader import render_to_string
from django.conf import settings


class User(AbstractUser):
    last_event_stream = models.DateTimeField(auto_now_add=True)

    def has_stream_notifications(self):
        return user_streams.get_stream_items(self).filter(seen=False).exists()

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super(User, self).save(*args, **kwargs)
        if is_new:
            template = 'account/activity-feed/new-user.html'
            context = {'user': self}
            users = [self]
            content = render_to_string(template, context)
            user_streams.add_stream_item(users, content)


class PublicKey(models.Model):
    """We store a representation of the public keys in the database. This is
    used to display and manage the keys without interacting with the server
    directly. When a key is created then it is stored on the server as its
    raw public key--operating under the respective and authorized user.

    Two users are required for operating on the server. The regular git user,
    which is the user whom manages the actual commands, and a very limited
    llab-www user whom just populates temporary files for the git user to read.

    The git user can read llab-www user's home directory, but the llab-www
    user can not do the inverse.

    """
    name = models.SlugField()
    _key = models.TextField()
    user = models.ForeignKey(User, related_name='public_keys')
    _key_changed = False

    def decrypt(self):
        from utils import cipher
        return cipher.decrypt(self._key, password='')

    def encrypt(self, key):
        from utils import cipher
        encrypt = cipher.encrypt(key, password='')
        self._key_changed = True
        return encrypt

    def save(self, *args, **kwargs):
        super(PublicKey, self).save(*args, **kwargs)
        if self._key_changed:
            from utils import gitolite
            gitolite.add_key(self)

auth_models.User = User
