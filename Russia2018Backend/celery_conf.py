from __future__ import absolute_import
import os
import django

from celery import Celery
from django.conf import settings



# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Russia2018Backend.settings')
app = Celery('Russia2018Backend')

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings', namespace='CELERY')
print("[celery_config]> Looking for tasks in: %s" % settings.INSTALLED_APPS)
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS, force=True) # Force = True is key for Django 2.0

