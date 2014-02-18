from django import forms

from .models import User
from organization.models import Organization


class UserForm(forms.ModelForm):
    """A form for creating new users. Includes all the required
    fields, plus a repeated password."""
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation',
                                widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('username', 'email')

    def clean_user(self):
        super(UserForm, self).clean_user()
        username = self.cleaned_data['username']

        # Prevent any conflicting usernames from the urls.py
        bad_usernames = ('new', 'admin', 'account')
        if username in bad_usernames:
            raise forms.ValidationError('This username is already taken')

        # Prevent any overlap of organizations
        if Organization.objects.filter(name=username).exists():
            raise forms.ValidationError(('An organization exists with '
                                         'this name.'))

        return username

    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Passwords don\'t match')
        return password2

    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super(UserForm, self).save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user
