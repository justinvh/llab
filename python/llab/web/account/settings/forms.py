from django import forms
from django.core import exceptions
from django.utils.translation import ugettext as _

from .models import PublicKey, Profile, EmailAccount


class PublicKeyForm(forms.ModelForm):

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(PublicKeyForm, self).__init__(*args, **kwargs)

    def clean_name(self):
        name = self.cleaned_data['name']
        if PublicKey.objects.filter(name=name, user=self.user).exists():
            message = _('A public key already exists with this name')
            raise exceptions.ValidationError(message)
        return name

    def save(self, user=None, commit=True):
        public_key = super(PublicKeyForm, self).save(commit=False)
        public_key.key = self.cleaned_data['_key'].strip()
        public_key.user = user if user else public_key.user
        if commit:
            public_key.save()
        return public_key

    class Meta:
        model = PublicKey
        exclude = ('user', 'sha1sum')



class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        exclude = ('_participating', '_watching', 'user')


class EmailAccountForm(forms.ModelForm):
    class Meta:
        model = EmailAccount
        exclude = ('user',)
