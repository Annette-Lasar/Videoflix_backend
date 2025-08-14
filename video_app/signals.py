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
    Bei neuem Video (oder wenn die Datei gewechselt wurde) wird EIN Job enqueued.
    """
    # Enqueue nur, wenn eine Datei vorhanden ist
    if not instance.video_file:
        return

    # Nur beim Erstellen starten – oder wenn du auch bei Dateiwechsel willst:
    if created:
        logger.info("New video created -> enqueue processing for %s", instance.id)
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
