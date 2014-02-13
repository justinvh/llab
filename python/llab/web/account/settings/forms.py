from django import forms

from .models import PublicKey


class PublicKeyForm(forms.ModelForm):
    class Meta:
        model = PublicKey
