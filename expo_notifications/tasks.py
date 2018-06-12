from celery import task
from exponent_server_sdk import PushClient, PushServerError, PushMessage
from requests import HTTPError


@task
def send_push_messages_task(tokens, title, message):
    try:
        print("[send_push_messages_task]> Preparing messages..")
        messages = [
            PushMessage(
                to=token,
                title=title,
                body=message,
                priority="high",
                sound="default",
                data=None
            )
            for token in tokens
        ]
        print("[send_push_messages_task]> Sending push notifications..")
        response = PushClient().publish_multiple(push_messages=messages)
    except PushServerError as exc:
        # Encountered some likely formatting/validation error.
        print(exc)
    except (ConnectionError, HTTPError) as exc:
        # Encountered some Connection or HTTP error - retry a few times in
        # case it is transient.
        print(exc)
