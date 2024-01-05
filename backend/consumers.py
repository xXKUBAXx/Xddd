from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from django.template.loader import get_template


class NotificationConsumer(WebsocketConsumer):
    def connect(self):
        self.GROUP_NAME = 'user-notifications'
        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.GROUP_NAME, self.channel_name
        )
        self.accept()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.GROUP_NAME, self.channel_name
        )

    def notification(self, event):
        html = get_template("partials/notification.html").render(
            context=event
        )
        self.send(text_data=html)


class BannerConsumer(WebsocketConsumer):
    def connect(self):
        self.GROUP_NAME = 'user-banners'
        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.GROUP_NAME, self.channel_name
        )
        self.accept()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.GROUP_NAME, self.channel_name
        )

    def banner(self, event):
        html = get_template("partials/banner.html").render(
            context=event
        )
        self.send(text_data=html)

class LinksConsumer(WebsocketConsumer):
    def connect(self):
        self.GROUP_NAME = 'user-links'
        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.GROUP_NAME, self.channel_name
        )
        html = get_template("partials/links_ul.html").render(
            context={"id": self.scope['client'][-1]}
        )
        self.accept()
        self.send(text_data=html)

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.GROUP_NAME, self.channel_name
        )

    def link_created(self, event):
        html = get_template("partials/link_results.html").render(
            context={"keyword": event["keyword"], "id": event["id"], "channel_id": event["ul_id"]}
        )
        self.send(text_data=html)

    def link_done(self, event):
        html = get_template("partials/link_results.html").render(
            context={"keyword": event["keyword"], "url": event["url"], "id": event["id"]}
        )
        self.send(text_data=html)