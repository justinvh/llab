from django import forms

from .models import PublicKey, Profile, EmailAccount


class PublicKeyForm(forms.ModelForm):
    class Meta:
        model = PublicKey


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        exclude = ('_participating', '_watching', 'user')


class EmailAccountForm(forms.ModelForm):
    class Meta:
        model = EmailAccount
        exclude = ('user',)
