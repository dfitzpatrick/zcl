from django.conf.urls import url

from . import consumers

websocket_urlpatterns = [
    url(r'^notifications/$', consumers.NotificationConsumer),
    url(r'^events/(?P<streamer_id>\d+)/$', consumers.StreamerConsumer),
]
