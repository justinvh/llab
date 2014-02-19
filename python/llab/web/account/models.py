import user_streams

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth import models as auth_models

from llab.utils.request import notify_users


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
        template = 'account/activity-feed/user-new.html'
        context = {'user': self}
        notify_users(self, template, context)

        # Create the initial profile for the user
        from account.settings.models import Profile
        Profile.objects.create(user=self, _participating=0, _watching=0)

        # Create the initial email bindings if the email is provided for
        # this account. The initial email, if available is always the primary
        from account.settings.models import EmailAccount
        if self.email:
            EmailAccount.objects.create(
                user=self, email=self.email, primary=True)


auth_models.User = User
