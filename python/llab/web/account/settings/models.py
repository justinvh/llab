from django.db import models
from django.utils.translation import ugettext as _

from .fields import PublicKeyField
from django.conf import settings

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
