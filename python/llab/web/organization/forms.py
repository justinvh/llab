from django import forms

from organization.models import Organization, Group, Permission


class OrganizationForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = ('name',)

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
