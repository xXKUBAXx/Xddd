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

    def link_created(self, event):
        print(self.scope['user'].email, event['user'])
        html = get_template("partials/notification.html").render(
            context={"keyword": event["keyword"]}
        )
        self.send(text_data=html)
        html = get_template("partials/link_results.html").render(
            context={"keyword": event["keyword"], "id": event["id"]}
        )
        self.send(text_data=html)

    def link_done(self, event):
        html = get_template("partials/notification.html").render(
            context={"keyword": event["keyword"], "url": event["url"]}
        )
        self.send(text_data=html)
        html = get_template("partials/link_results.html").render(
            context={"keyword": event["keyword"], "url": event["url"], "id": event["id"]}
        )
        self.send(text_data=html)