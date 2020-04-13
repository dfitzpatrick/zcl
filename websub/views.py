import logging

from django.http import HttpResponse
from django.utils.decorators import classonlymethod
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from websub.models import Subscription
from . import signals

log = logging.getLogger('zcl.websub')

class WebSubView(APIView):
    """
    Handles the callback functions of subscribing and retrieving updates
    from the WebSub specification
    """
    @classonlymethod
    def as_view(cls, webhook_name, **initkwargs):
        """
        Assigns a name to the route which is sent via signal
        Parameters
        ----------
        event_task
        initkwargs

        Returns
        -------

        """
        cls.webhook_name = webhook_name
        result = super(WebSubView, cls).as_view(**initkwargs)
        return result

    def get(self, request, *args, **kwargs):
        """
        GET request by a hub. This parses the different required parameters.

        Parameters
        ----------
        request
        args
        kwargs

        Returns
        -------
        HttpResponse
        """
        required = ['hub.topic', 'hub.mode', 'hub.challenge']
        topic = request.GET.get('hub.topic')
        mode = request.GET.get('hub.mode')

        if any(request.GET.get(attr) is None for attr in required):
            log.error("Callback missing Attributes. Returning BAD_REQUEST")
            return Response(status=status.HTTP_400_BAD_REQUEST)
        try:
            sub = Subscription.objects.get(topic=topic)
            uuid = sub.uuid
        except Subscription.DoesNotExist:
            log.error(f"Subscription Model for {topic} does not exist. Returning BAD_REQUEST")
            return Response(status=status.HTTP_400_BAD_REQUEST)

        response = self.handshake(request, *args, sub=sub, **kwargs)
        log.debug(f"Sent Challenge Response {mode} for {topic}")

        if mode == 'unsubscribe':
            # Delete the subscription object
            sub.delete()
            log.debug(f"Deleted Subscription {uuid}")
        return response

    def post(self, request, *args, **kwargs):
        """
        Data was received from the webhook. Dispatch to the event_task
        That will process it.
        Parameters
        ----------
        request
        args
        kwargs

        Returns
        -------
        Http OK
        """
        log.debug(f"Received Webhook Update for {self.webhook_name} Data: {request.data}")
        signals.webhook_update.send(sender=self.__class__, webhook_name=self.webhook_name, uuid=kwargs.get('id'), data=request.data)
        return Response(status=status.HTTP_200_OK)

    def handshake(self, request, *args, **kwargs):
        """
        Handshake logic.

        Todo: Put validation logic here to accept or decline the request.
        Parameters
        ----------
        request
        args
        kwargs

        Returns
        -------

        """
        sub = kwargs.get('sub')
        challenge = request.GET['hub.challenge']
        response = HttpResponse(
            challenge,
            content_type="text/plain"
        )

        signals.new_webhook.send(sender=self.__class__, sub=sub)
        return response
