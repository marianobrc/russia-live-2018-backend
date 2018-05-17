from django.db import models


class PushToken(models.Model):
    token = models.CharField(max_length=2000, unique=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.token
