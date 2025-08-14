from django.db import models
from pathlib import Path
from django.contrib.auth.models import User
from utils.data import RESOLUTION_CHOICES
from utils.videos import video_upload_to


class Video(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    thumbnail_url = models.URLField(blank=True, null=True)
    category = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    video_file = models.FileField(upload_to=video_upload_to, blank=True, null=True)

    PROCESSING_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]
    processing_status = models.CharField(max_length=12, choices=PROCESSING_CHOICES, default="pending")
    processing_progress = models.PositiveIntegerField(default=0)  # 0–100
    processing_error = models.TextField(blank=True, null=True)

    duration_seconds = models.PositiveIntegerField(blank=True, null=True)
    file_size_mb = models.PositiveIntegerField(blank=True, null=True)

    def __str__(self):
        return self.title
    

class VideoStreamVariant(models.Model):
    video = models.ForeignKey(
        Video, related_name='variants', on_delete=models.CASCADE)
    resolution = models.CharField(max_length=10, choices=RESOLUTION_CHOICES)
    manifest_path = models.FilePathField(
        path='/app/media/hls_manifests/', match=r".*\.m3u8$", recursive=True)

    class Meta:
        unique_together = ('video', 'resolution')

    def __str__(self):
        return f"{self.video.title} - {self.resolution}"


class UserWatchProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    video = models.ForeignKey(
        Video, on_delete=models.CASCADE)
    resolution = models.CharField(max_length=10, choices=RESOLUTION_CHOICES)
    last_position_seconds = models.PositiveIntegerField()
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'video', 'resolution')

    def __str__(self):
        return f"{self.user.username} - {self.video.title} ({self.resolution}) @ {self.last_position_seconds}s"
