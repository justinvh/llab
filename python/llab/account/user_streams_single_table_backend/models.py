from django.db import models
from llab import settings


class StreamItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='+')
    content = models.TextField()
    created_at = models.DateTimeField()
    seen = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
