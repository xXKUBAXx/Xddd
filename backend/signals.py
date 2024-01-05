from .models import Link, Banner
from django.db.models.signals import post_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


@receiver(post_save, sender=Link)
def create_profile(sender, instance, created, **kwargs):
    if created:
        # trigger notification to all consumers in the 'user-notification' group
        channel_layer = get_channel_layer()
        group_name = 'user-links'
        event = {
            "type": "link_created",
            "user": instance.user,
            "task_id": instance.task_id, 
            "ul_id": instance.ul_id,
            "keyword": instance.keyword,
            "id": instance.id
        }
        async_to_sync(channel_layer.group_send)(group_name, event)
    
    else:
        channel_layer = get_channel_layer()
        group_name = 'user-links'
        event = {
            "type": "link_done", 
            "user": instance.user,
            "task_id": instance.task_id, 
            "keyword": instance.keyword,
            "url": instance.url,
            "id": instance.id
        }
        async_to_sync(channel_layer.group_send)(group_name, event)



@receiver(post_save, sender=Banner)
def db_notificatoin(sender, instance, created, **kwargs):
    if instance.active:
        channel_layer = get_channel_layer()
        group_name ='user-banners' 
        event = {
            "type": "banner", 
            "text": instance.text,
            "color": instance.color
        }
        async_to_sync(channel_layer.group_send)(group_name, event)