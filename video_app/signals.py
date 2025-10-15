import os
from .models import Video
from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete
from .tasks import queue_video_processing
from django.conf import settings
from urllib.parse import urlparse
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
    Deletes file and thumbnail from filesystem
    when corresponding 'Video' object is deleted.
    """
    logger.info("post_delete triggered for Video ID %s", instance.id)
    
    if instance.video_file and os.path.isfile(instance.video_file.path):
        try:
            os.remove(instance.video_file.path)
            logger.info("Deleted video file: %s", instance.video_file.path)
        except Exception as e:
            logger.warning(
                "Could not delete video file %s: %s", instance.video_file.path, e)

    if instance.thumbnail_url:
        parsed = urlparse(instance.thumbnail_url)
        thumb_path = parsed.path.replace("/media/", "", 1)
        thumb_full_path = os.path.join(settings.MEDIA_ROOT, thumb_path)

        if os.path.isfile(thumb_full_path):
            try:
                os.remove(thumb_full_path)
                logger.info("Deleted thumbnail: %s", thumb_full_path)
            except Exception as e:
                logger.warning(
                    "Could not delete thumbnail: %s: $s", thumb_full_path, e)

        else:
            logger.info("Thumbnail file not found: %s", thumb_full_path)
