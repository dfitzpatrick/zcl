import logging
from uuid import uuid4

from django.db import models

log = logging.getLogger('zcl.websub')


class Subscription(models.Model):
    """
    This will represent a subscription is a WebSub spec

    """
    hub = models.URLField()
    topic = models.URLField()
    callback_name = models.CharField(max_length=100)
    lease_expiration = models.DateTimeField(null=True, blank=True)
    uuid = models.UUIDField(blank=True, null=True)

    def __str__(self):
        return self.topic

    def unsubscribe(self, **kwargs):
        from .tasks import subscription_update
        subscription_update.delay(self.pk, 'unsubscribe', **kwargs)

    def refresh(self, **kwargs):
        from .tasks import subscription_update
        subscription_update.delay(self.pk, 'subscribe', refresh=True, **kwargs)

    @classmethod
    def subscribe(cls, hub, topic, callback_name, **kwargs) -> None:
        """
        Populates the model with information and starts a background task
        that will start the handshake with the Publisher.
        Parameters
        ----------
        hub
        topic
        callback_name
        resubscribe

        Returns
        -------

        """

        from .tasks import subscription_update
        uuid = uuid4()
        sub, created = cls.objects.get_or_create(
            hub=hub,
            topic=topic,
            callback_name=callback_name,
            defaults = {
                'uuid': uuid
            }
        )
        if created:
            log.debug(f"Sending to Celery 'subscribe' to {topic}")
            subscription_update.delay(sub.pk, 'subscribe', **kwargs)
        return sub
