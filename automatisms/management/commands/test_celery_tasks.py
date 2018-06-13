from django.core.management.base import BaseCommand
from automatisms.tasks import test_task


class Command(BaseCommand):
    """
    Run a test task in celery
    """

    help = 'Run a test task in celery'

    def handle(self, *args, **options):
        test_task.delay()
