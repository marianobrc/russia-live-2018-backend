# -*- coding: UTF-8 -*-
from django.core.management.base import BaseCommand
from expo_notifications.core import send_push_message_broadcast


class Command(BaseCommand):
    """
    Send a push notification to one specific device
    """

    help = 'Send a push notification to one specific device'

    def add_arguments(self, parser):
        parser.add_argument('--tokens', dest='token_list_str', help='device token list separated by pipe')
        parser.add_argument('--title', dest='title', help='notification title')
        parser.add_argument('--message', dest='message', help='notification text')

    def handle(self, *args, **options):
        try:
            token_list_str = options['token_list_str']
            token_list = token_list_str.split('|')
            title = options['title']
            message = options['message']
        except Exception as e:
            print("Error parsing parameters %s" % e)
            exit(1)
        else:
            send_push_message_broadcast(token_list=token_list, title=title, message=message)
        finally:
            print("Done.")




