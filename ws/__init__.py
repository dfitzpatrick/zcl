import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import json

import ws.types

CACHE = []
CACHE_MAX_SIZE = 15

log = logging.getLogger(__name__)

def make_unique_stub(payload):
    data = payload['payload']
    stub = {
        'type': payload['type'],
        'time': payload['time'],
        'game_id': payload['game_id']
    }
    return stub

def send_notification(action_type, payload):
    global CACHE
    stub = make_unique_stub(payload)
    if stub in CACHE:
        return

    channel_layer = get_channel_layer()
    print("Sending notification")
    log.info("Sending notification")
    async_to_sync(channel_layer.group_send)(
        'notifications',
        {
            'type': action_type,
            'action': action_type,
            'guild': 476518371320397834,
            'payload': payload
        }
    )
    CACHE = CACHE[:CACHE_MAX_SIZE - 1] + [stub]
