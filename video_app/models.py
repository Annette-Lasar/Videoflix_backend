from django.db import models
from pathlib import Path
from django.contrib.auth.models import User
from utils.data import RESOLUTION_CHOICES, PROCESSING_CHOICES
from utils.videos import video_upload_to


class Video(models.Model):
    """
    Represents an uploaded video with metadata and processing state.

    Processing-related Fields:
        processing_status (CharField): Current processing state 
            (pending, processing, completed, failed).
        processing_progress (PositiveIntegerField): Progress percentage of processing.
        processing_error (TextField): Error message if processing failed.
        duration_seconds (PositiveIntegerField): Duration of the video in seconds.
        file_size_mb (PositiveIntegerField): File size of the video in MB.
    """
    title = models.CharField(max_length=255)
    description = models.TextField()
    thumbnail_url = models.URLField(blank=True, null=True)
    category = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    video_file = models.FileField(
        upload_to=video_upload_to, blank=True, null=True)

    processing_status = models.CharField(
        max_length=12, choices=PROCESSING_CHOICES, default="pending")
    processing_progress = models.PositiveIntegerField(default=0)
    processing_error = models.TextField(blank=True, null=True)

    duration_seconds = models.PositiveIntegerField(blank=True, null=True)
    file_size_mb = models.PositiveIntegerField(blank=True, null=True)

    def __str__(self):
        return self.title


class VideoStreamVariant(models.Model):
    """
    Represents a transcoded variant of a video at a specific resolution.

    Each variant points to an HLS manifest file ('.m3u8') 
    that defines the stream segments for this resolution.

    Relations:
        video (ForeignKey): The original Video object this variant belongs to.
        resolution (CharField): Resolution of the variant 
            (e.g., 360p, 480p, 720p, 1080p).
        manifest_path (FilePathField): Path to the corresponding HLS manifest file.

    Constraints:
        unique_together: Ensures that each video has only one variant per resolution.
    """
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
    """
    Tracks a user's watch progress for a specific video and resolution.

    Relations:
        user (ForeignKey): The user who is watching the video.
        video (ForeignKey): The video being watched.
        resolution (CharField): Resolution at which the video was played.

    Fields:
        last_position_seconds (PositiveIntegerField): 
            Last playback position in seconds where the user stopped watching.
        updated_at (DateTimeField): 
            Timestamp automatically updated when the progress is saved.

    Constraints:
        unique_together: Ensures a user has only one progress entry 
        per video and resolution.
    """
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
