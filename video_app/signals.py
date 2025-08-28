import os
from .models import Video
from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete
from .tasks import queue_video_processing
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Video)
def video_post_save(sender, instance: Video, created, **kwargs):
    """
    When a new video is created (or when the file has been replaced),
    a single processing job is enqueued.
    """
    if not instance.video_file:
        return

    if created:
        logger.info(
            "New video created -> enqueue processing for %s", instance.id)
        queue_video_processing(instance.id)


@receiver(post_delete, sender=Video)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """
    Deletes file from filesystem
    when corresponding 'Video' object is deleted.
    """
    if instance.video_file:
        if os.path.isfile(instance.video_file.path):
            os.remove(instance.video_file.path)
