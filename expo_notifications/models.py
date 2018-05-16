from django.db import models


class PushToken(models.Model):
    token = models.CharField(max_length=2000)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.token
