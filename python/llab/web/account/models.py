import user_streams

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth import models as auth_models
from django.template.loader import render_to_string


class User(AbstractUser):
    last_event_stream = models.DateTimeField(auto_now_add=True)

    def has_stream_notifications(self):
        return user_streams.get_stream_items(self).filter(seen=False).exists()

    def greetings(self):
        name = self.profile.name.split(' ')[0] if self.profile.name else None
        return name or self.username

    def greetings_formal(self):
        return self.profile.name or self.username

    def gravatar(self):
        return self.profile.gravatar or self.email

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super(User, self).save(*args, **kwargs)

        # New users have a special bit of code to jump through
        if not is_new:
            return

        # Demonstrate that the activity-feed is working
        template = 'account/activity-feed/new-user.html'
        context = {'user': self}
        users = [self]
        content = render_to_string(template, context)
        user_streams.add_stream_item(users, content)

        # Create the initial profile for the user
        from account.settings.models import Profile
        Profile.objects.create(user=self, _participating=0, _watching=0)


auth_models.User = User
