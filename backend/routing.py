from django.urls import path

from . import consumers

websocket_urlpatterns = [
    path("ws/notifications/", consumers.NotificationConsumer.as_asgi()),
    path("ws/banners/", consumers.BannerConsumer.as_asgi()),
    path("ws/links/", consumers.LinksConsumer.as_asgi())
]