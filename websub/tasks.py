import logging

import requests
from celery import shared_task
from django.conf import settings
from django.urls import reverse
from celery.utils.log import get_task_logger
from .models import Subscription
import json

log = get_task_logger('celery.zcl.websub')

@shared_task
def subscribe(pk, uuid, *args, **kwargs):
    """
    Starts the handshaking process based on the model that was created.
    Parameters
    ----------
    pk
    uuid

    Returns
    -------

    """
    sub = Subscription.objects.get(pk=pk)
    callback_url = settings.SITE_URL + reverse(sub.callback_name, args=[uuid])
    payload = {
        'hub.mode': 'subscribe',
        'hub.topic': sub.topic,
        'hub.callback': callback_url,
        'hub.lease_seconds': kwargs.get('lease_seconds') or 864000
    }
    response = requests.post(sub.hub, payload, **kwargs)
    log.debug(f"Subscribe (Resp {response.status_code}) Topic: {sub.topic} Callback: {callback_url}")

@shared_task
def subscription_update(pk: int, hub_mode: str, refresh: bool = False, **kwargs):
    sub = Subscription.objects.get(pk=pk)
    callback_url = settings.PUBLIC_SITE_URL + reverse(sub.callback_name, args=[sub.uuid])
    payload = {
        'hub.mode': hub_mode,
        'hub.topic': sub.topic,
        'hub.callback': callback_url,
    }
    user_headers = kwargs.get('headers', {})
    if 'Content-Type' not in user_headers.keys():
        user_headers['Content-Type'] = 'application/json'
        kwargs['headers'] = user_headers

    # Should be ignored per WebSub standard. Better to be explicit though.
    if hub_mode == "subscribe":
        payload['hub.lease_seconds'] = kwargs.get('lease_seconds') or 864000
    response = requests.post(sub.hub, data=json.dumps(payload), **kwargs)
    if refresh:
        # Just for logging
        hub_mode = 'refresh'
    print(f"{hub_mode} (Resp {response.status_code})  Mode: {hub_mode} Hub: {sub.hub} Payload: {payload}")
    print(response.text)


