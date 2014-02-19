from django import forms

from .models import PublicKey, Profile, EmailAccount


class PublicKeyForm(forms.ModelForm):
    class Meta:
        model = PublicKey
        exclude = ('user', 'sha1sum')

    def save(self, user=None, commit=True):
        public_key = super(PublicKeyForm, self).save(commit=False)
        public_key.key = self.cleaned_data['_key']
        public_key.user = user if user else public_key.user
        if commit:
            public_key.save()
        return public_key


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        exclude = ('_participating', '_watching', 'user')


class EmailAccountForm(forms.ModelForm):
    class Meta:
        model = EmailAccount
        exclude = ('user',)
