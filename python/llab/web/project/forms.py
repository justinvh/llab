from django import forms
from .models import Project


class ProjectForm(forms.ModelForm):
    """The form responsible for creating new projects.

    The Project model will handle creating the necessary Git projects in
    the defined repository. See settings.py for repository information.

    """
    class Meta:
        model = Project
        fields = ('name', 'description', 'private')

    def save(self, owner, fork=None, commit=True, *args, **kwargs):
        """save -> Project.

        Assigns the about-to-be-created a user as an owner.

        """
        project = super(ProjectForm, self).save(commit=False)
        project.owner = owner
        project.fork = fork
        if commit:
            project.save()
        return project
