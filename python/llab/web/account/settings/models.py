from django.db import models
from django.utils.translation import ugettext as _

from account.models import User
from .fields import PublicKeyField
from django.conf import settings

from llab.utils.enumeration import make_bitwise_enumeration, BitwiseSet
from llab.utils.request import notify_users


Notification = make_bitwise_enumeration('Notification', ('email', 'web'))


# This is the key manager--or the gate-keeper
module = settings.SSH_KEY_MANAGEMENT_BACKEND
ssh_manager =  __import__(module, globals(), locals(), ['run', 'delete'], -1)


class Profile(models.Model):
    user = models.OneToOneField(User)
    name = models.CharField(max_length=255, blank=True)
    url = models.URLField(blank=True)
    company = models.CharField(max_length=255, blank=True)
    location = models.CharField(max_length=255, blank=True)
    gravatar = models.EmailField(blank=True)
    _participating = models.IntegerField()
    _watching = models.IntegerField()

    @property
    def participating(self):
        return BitwiseSet(self, '_pmap', Notification)
        if hasattr(self, '_pmap'):
            return self._pmap
        self._pmap = BitwiseSet(Notification, self, '_participating')
        for permission, value in Notification.choices:
            if self._participating & value:
                self._pmap.add(getattr(Notification, permission))
        return self._pmap

    @participating.setter
    def participating(self, permission_set):
        self._participating = 0
        for value in permission_set:
            self._participating |= value

    @property
    def watching(self):
        return BitwiseSet(self, '_wmap', Notification)
        if hasattr(self, '_wmap'):
            return self._wmap
        self._wmap = BitwiseSet(Notification, self, '_watching')
        for permission, value in Notification.choices:
            if self._watching & value:
                self._wmap.add(getattr(Notification, permission))
        return self._wmap

    @watching.setter
    def watching(self, permission_set):
        self._watching = 0
        for value in permission_set:
            self._watching |= value


class EmailAccount(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, related_name='email_accounts')
    email = models.EmailField()
    primary = models.BooleanField()


class PublicKey(models.Model):
    name = models.SlugField()
    created = models.DateTimeField(auto_now_add=True)
    _key = PublicKeyField(verbose_name=_('Key'), db_index=True)
    sha1sum = models.CharField(max_length=60)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             related_name='public_keys')

    class Meta:
        unique_together = ('user', 'name')

    @property
    def key(self):
        return self.decrypt()

    @key.setter
    def key(self, value):
        value = PublicKey.prepare_key(value)
        self._key = self.encrypt(value)

    @classmethod
    def prepare_key(cls, value):
        lines = value.strip().split("\n")
        lines = (" ".join(line.strip().split()) for line in lines)
        value = "\n".join(line for line in lines if line)
        value = ' '.join(value.split(' ')[:2])
        return value

    def decrypt(self):
        from llab.utils import cipher
        return cipher.decrypt(self._key, password='')

    def encrypt(self, key):
        from llab.utils import cipher
        encrypt, sha1sum = cipher.encrypt(key, password='')
        self._key = encrypt
        self.sha1sum = sha1sum
        return encrypt

    def delete(self, *args, **kwargs):
        # Make sure that the user knows about the key being deleted
        user = self.user
        template = 'settings/activity-feed/public-key-delete.html'
        context = {'user': user, 'public_key': self}
        notify_users(user, template, context)
        super(PublicKey, self).delete(*args, **kwargs)

        # Remove the key from the backend
        ssh_manager.delete(self)

    def save(self, *args, **kwargs):
        super(PublicKey, self).save(*args, **kwargs)

        # Make sure that the user knows about the key being added
        user = self.user
        template = 'settings/activity-feed/public-key-new.html'
        context = {'user': user, 'public_key': self}
        notify_users(user, template, context)

        # Now use the registered SSH backend for installing the
        # public key for this user.
        ssh_manager.run(self)
