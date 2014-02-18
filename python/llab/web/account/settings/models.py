from django.db import models
from django.utils.translation import ugettext as _

from account.models import User
from .fields import PublicKeyField
from django.conf import settings

from llab.utils.enumeration import make_bitwise_enumeration, BitwiseSet


Notification = make_bitwise_enumeration('Notification', ('email', 'web'))


class Profile(models.Model):
    user = models.OneToOneField(User)
    name = models.CharField(max_length=255)
    url = models.URLField()
    company = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    gravatar = models.EmailField()
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
    user = models.ForeignKey(User, related_name='email_accounts')
    email = models.EmailField()
    primary = models.BooleanField()


class PublicKey(models.Model):
    name = models.SlugField()
    _key = PublicKeyField(verbose_name=_('Key'))
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             related_name='public_keys')
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
