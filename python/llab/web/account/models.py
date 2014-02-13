import user_streams

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth import models as auth_models
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _
from django.conf import settings


class User(AbstractUser):
    last_event_stream = models.DateTimeField(auto_now_add=True)

    def has_stream_notifications(self):
        return user_streams.get_stream_items(self).filter(seen=False).exists()

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super(User, self).save(*args, **kwargs)
        if is_new:
            template = 'account/activity-feed/new-user.html'
            context = {'user': self}
            users = [self]
            content = render_to_string(template, context)
            user_streams.add_stream_item(users, content)


auth_models.User = User
