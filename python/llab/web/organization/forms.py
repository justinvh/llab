from django import forms

from account.models import User
from .models import Organization, Group, Permission, Role


class OrganizationForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = ('name',)

    def clean_name(self):
        name = self.cleaned_data['name']
        # Prevent any conflicting organizations from the urls.py
        bad_organizations = ('new', 'admin', 'account')
        if name in bad_organizations:
            raise forms.ValidationError('This organization is already taken')

        # Prevent any overlap of users
        if User.objects.filter(username=name).exists():
            raise forms.ValidationError('A user exists with this name.')
        return name


    def save(self, owner, commit=True, *args, **kwargs):
        obj = super(OrganizationForm, self).save(*args, commit=False, **kwargs)
        obj.owner = owner
        if commit:
            obj.save()
        return obj


class GroupForm(forms.ModelForm):
    permissions = forms.MultipleChoiceField(Permission.choices, required=False)
    predefined = forms.ModelChoiceField(queryset=Group.objects.none())

    def __init__(self, organization, *args, **kwargs):
        super(GroupForm, self).__init__(*args, **kwargs)
        self.fields['predefined'].queryset = organization.groups.all()

    class Meta:
        model = Group
        fields = ('name',)


class RoleForm(forms.ModelForm):
    group = forms.ModelChoiceField(queryset=Group.objects.none())
    user = forms.CharField(max_length=255)

    def __init__(self, organization, *args, **kwargs):
        super(RoleForm, self).__init__(*args, **kwargs)
        self.organization = organization
        self.fields['group'].queryset = organization.groups.all()

    def clean_user(self):
        user = self.cleaned_data['user']
        org = self.organization
        try:
            user = User.objects.get(username=user)
            self.cleaned_user = user
            if False and org.owner == user:
                msg = '{} is already the owner of the {} organization.'
                raise forms.ValidationError(msg.format(user, org.name))
            elif org.roles.filter(user=user).exists():
                msg = '{} is already a member of the {} organization.'
                raise forms.ValidationError(msg.format(user, org.name))
            return self.cleaned_data['user']
        except User.DoesNotExist:
            raise forms.ValidationError('{} was not found.'.format(user))

    def save(self, commit=True):
        role = Role(organization=self.organization,
                    user=self.cleaned_user,
                    group=self.cleaned_data['group'])
        if commit:
            return role.save()
        return role

    class Meta:
        model = Role
        exclude = ['user', 'organization']
