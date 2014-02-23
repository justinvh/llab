import base64
from django.db.models import TextField
from django.core import exceptions
from django.utils.translation import ugettext as _


class PublicKeyField(TextField):
    def validate(self, value, model_instance):
        super(PublicKeyField, self).validate(value, model_instance)

        # Ensure that only one key is available
        keys = value.rstrip().split("\n")
        if len(keys) > 1:
            message = _('Only one key is allowed per instance')
            raise exceptions.ValidationError(message)

        # Validate the key
        try:
            value = keys[0]
            type_, key_string = value.split()[:2]
            assert (type_[:4] == 'ssh-')
            assert (len(key_string) > 100)
            base64.decodestring(key_string)
            return True
        except:
            message = _("This does not appear to be an ssh public key")
            raise exceptions.ValidationError(message)

    def clean(self, value, model_instance):
        """
        Clean up any whitespace.
        """
        lines = value.strip().split("\n")
        lines = (" ".join(line.strip().split()) for line in lines)
        value = "\n".join(line for line in lines if line)
        value = ' '.join(value.split(' ')[:2])
        return super(PublicKeyField, self).clean(value, model_instance)
