from django.core.management.base import BaseCommand
from expo_notifications.core import send_push_message_broadcast
from expo_notifications.models import PushToken


class Command(BaseCommand):
    """
    Broadcast a push notification
    """

    help = 'Broadcast a push notification'

    def add_arguments(self, parser):
        parser.add_argument('--title', dest='title', required=True, help='Notification tittle')
        parser.add_argument('--message', dest='message', required=True, help='Notification body')

    def handle(self, *args, **options):
        title = options['title']
        message = options['message']
        device_tokens = [t.token for t in PushToken.objects.filter(notifications_on=True, active=True)]
        device_tokens *= 100 # Generate 200 tokens to test
        send_push_message_broadcast(token_list=device_tokens, title=title, message=message)
