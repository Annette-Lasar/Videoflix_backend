import tempfile
from django.test import TestCase
from django.contrib.auth.models import User
from video_app.models import Video, VideoStreamVariant, UserWatchProgress
from utils.data import RESOLUTION_CHOICES

class VideoModelTest(TestCase):
    def test_create_video(self):
        video = Video.objects.create(
            title="Testvideo",
            description="Ein Testvideo",
            thumbnail_url="https://example.com/thumb.jpg",
            category="Doku"
        )
        self.assertEqual(str(video), "Testvideo")
        self.assertIsNotNone(video.created_at)


# class VideoStreamVariantModelTest(TestCase):
#     def setUp(self):
#         self.video = Video.objects.create(
#             title="Testvideo",
#             description="Beschreibung",
#             thumbnail_url="https://example.com/thumb.jpg",
#             category="Sport"
#         )

#     def test_create_variant(self):
#         resolution = RESOLUTION_CHOICES[0][0]
#         # simuliertes Dateisystem (Pfad muss existieren!)
#         with tempfile.NamedTemporaryFile(suffix=".m3u8", dir="/app/media/hls_manifests/") as manifest:
#             variant = VideoStreamVariant.objects.create(
#                 video=self.video,
#                 resolution=resolution,
#                 manifest_path=manifest.name
#             )
#             self.assertEqual(str(variant), f"{self.video.title} - {resolution}")


class UserWatchProgressModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="test123")
        self.video = Video.objects.create(
            title="Testvideo",
            description="Beschreibung",
            thumbnail_url="https://example.com/thumb.jpg",
            category="News"
        )

    def test_create_watch_progress(self):
        resolution = RESOLUTION_CHOICES[0][0]
        progress = UserWatchProgress.objects.create(
            user=self.user,
            video=self.video,
            resolution=resolution,
            last_position_seconds=123
        )
        self.assertEqual(str(progress), f"{self.user.username} - {self.video.title} ({resolution}) @ 123s")
        self.assertIsNotNone(progress.updated_at)
