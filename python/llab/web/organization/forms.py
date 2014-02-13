from django import forms

from account.models import User
from organization.models import Organization, Group, Permission


class OrganizationForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = ('name',)

    def clean_name(self):
        super(OrganizationForm, self).clean_name()
        name = self.cleaned_data['name']
        # Prevent any conflicting organizations from the urls.py
        bad_organizations = ('new', 'admin', 'account')
        if name in bad_organizations:
            raise forms.ValidationError('This organization is already taken')

        # Prevent any overlap of users
        if User.objects.filter(username=name).exists():
            raise forms.ValidationError('A user exists with this name.')
        return username


    def save(self, owner, commit=False, *args, **kwargs):
        obj = super(OrganizationForm, self).save(*args, commit=False, **kwargs)
        if commit:
            obj.save()
        return obj


class GroupForm(forms.ModelForm):
    permissions = forms.MultipleChoiceField(Permission.choices, required=False)
    predefined = forms.ModelChoiceField(queryset=Group.objects.none())

    def __init__(self, predefined=Group.builtins(), *args, **kwargs):
        super(GroupForm, self).__init__(*args, **kwargs)
        self.fields['predefined'].queryset = predefined

    class Meta:
        model = Group
        fields = ('name',)
