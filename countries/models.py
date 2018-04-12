from django.db import models


# Create your models here.
class Country(models.Model):
    code_iso3 = models.CharField(max_length=3, unique=True, db_index=True)
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.code_iso3
