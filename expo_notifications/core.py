from itertools import islice

from exponent_server_sdk import DeviceNotRegisteredError
from exponent_server_sdk import PushClient
from exponent_server_sdk import PushMessage
from exponent_server_sdk import PushResponseError
from exponent_server_sdk import PushServerError
from requests.exceptions import ConnectionError
from requests.exceptions import HTTPError
from celery import task
from .tasks import send_push_messages_task

# Basic arguments. You should extend this function with the push features you
# want to use, or simply pass in a `PushMessage` object.
@task
def send_push_message(token, title, message, extra=None):
    try:
        response = PushClient().publish(
            PushMessage(to=token,
                        title=title,
                        body=message,
                        data=extra))
    except PushServerError as exc:
        # Encountered some likely formatting/validation error.
        raise exc
    except (ConnectionError, HTTPError) as exc:
        # Encountered some Connection or HTTP error - retry a few times in
        # case it is transient.
        raise exc

    try:
        # We got a response back, but we don't know whether it's an error yet.
        # This call raises errors so we can handle them with normal exception
        # flows.
        response.validate_response()
    except DeviceNotRegisteredError:
        # Mark the push token as inactive
        from .models import PushToken
        PushToken.objects.filter(token=token).update(active=False)
    except PushResponseError as exc:
        # Encountered some other per-notification error.
        raise exc





def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]


def send_push_message_broadcast(token_list, title, message):
    try:
        print("[send_push_message_broadcast]> Slicing messages list by 50..")
        MESSAGES_NUM = 50 # 50 BY GROUP
        spliced_tokens = list(chunks(token_list, MESSAGES_NUM))
        for tokens_group in spliced_tokens:
            send_push_messages_task.delay(tokens_group, title, message)
    except Exception as e:
        print("[send_push_message_broadcast]> ERROR: \n %s" % e )
        return
