import shutil
import tempfile
from pathlib import Path
from django.conf import settings
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import AccessToken
from video_app.models import Video, VideoStreamVariant
from unittest import mock


class VideoListViewTest(APITestCase):
    """Integration tests for the VideoListView endpoint."""

    def setUp(self):
        """Create a user, auth token, sample video, and base URL for requests."""
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123"
        )
        self.token = str(AccessToken.for_user(self.user))

        self.video = Video.objects.create(
            title="How to Python",
            description="A useful video about the most popular programming language.",
            thumbnail_url="https://via.placeholder.com/320x180.png?text=Test+Thumbnail",
            category="DIY"
        )

        self.url = reverse("video-list")

    def test_200_authenticated_user_gets_video_list(self):
        """200 OK: Authenticated user receives a non-empty video list."""
        self.client.cookies["access_token"] = self.token
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], self.video.title)

    def test_401_unauthenticated_user_cannot_access(self):
        """401 Unauthorized: Request without token is rejected."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_500_internal_server_error(self):
        """500 Internal Server Error: View returns 500 when DB access raises an exception."""
        self.client.cookies["access_token"] = self.token
        with mock.patch("video_app.models.Video.objects.all", side_effect=Exception("DB error")):
            resp = self.client.get(self.url)
        self.assertEqual(resp.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR)


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(prefix="test_media_"))
class VideoVariantManifestViewTests(APITestCase):
    """Integration tests for the video variant manifest endpoint."""
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.user = User.objects.create_user(username="u", password="p")
        token = AccessToken.for_user(self.user)
        self.token = str(token)  # ← das hat gefehlt!
        self.auth_headers = {"HTTP_AUTHORIZATION": f"Bearer {self.token}"}

        self.video = Video.objects.create(
            title="Dog Bowl", description="test",
        )

        self.url = lambda vid, res: reverse(
            "video-variant-manifest", args=[vid, res]
        )

    def _write_manifest(self, video_id: int, resolution: str, content: str = "#EXTM3U\n"):
        """
        Create directories and a dummy index.m3u8 file in MEDIA_ROOT.

        Returns:
            str: Relative manifest_path string, consistent with how the app stores it.
        """
        rel_path = Path("hls") / str(video_id) / resolution / "index.m3u8"
        abs_path = Path(settings.MEDIA_ROOT) / rel_path
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        abs_path.write_text(content, encoding="utf-8")
        return str(rel_path)

    # --- Tests ---

    def test_unauthenticated_returns_401(self):
        """401 Unauthorized: Request without auth token is rejected."""
        url = self.url(self.video.id, "480p")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invalid_resolution_returns_404(self):
        """404 Not Found: No variant exists for given video and resolution."""
        self.client.cookies["access_token"] = self.token
        url = self.url(self.video.id, "999p")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_variant_not_found_returns_404(self):
        """404 Not Found: Variant not found in DB."""
        url = self.url(self.video.id, "480p")
        self.client.cookies["access_token"] = self.token
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_manifest_missing_on_disk_returns_404(self):
        """404 Not Found: Variant exists in DB, but manifest file is missing on disk."""
        VideoStreamVariant.objects.create(
            video=self.video,
            resolution="480p",
            manifest_path=f"hls/{self.video.id}/480p/index.m3u8",
        )
        url = self.url(self.video.id, "480p")
        self.client.cookies["access_token"] = self.token
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_serves_manifest_with_correct_content_type_and_body(self):
        """200 OK: Returns manifest file with correct content type and body."""
        body = "#EXTM3U\n#EXT-X-VERSION:3\n"
        manifest_rel = self._write_manifest(
            self.video.id, "480p", content=body)

        VideoStreamVariant.objects.create(
            video=self.video,
            resolution="480p",
            manifest_path=manifest_rel,
        )

        url = self.url(self.video.id, "480p")
        self.client.cookies["access_token"] = self.token
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp["Content-Type"], "application/vnd.apple.mpegurl")
        content_bytes = b"".join(resp.streaming_content)
        self.assertEqual(content_bytes.decode("utf-8"), body)


# @override_settings(MEDIA_ROOT=tempfile.mkdtemp(prefix="test_media_"))
# class VideoSegmentViewTests(APITestCase):
#     """
#     Integration tests for the video segment endpoint.
#     """
#     @classmethod
#     def tearDownClass(cls):
#         shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
#         super().tearDownClass()

#     def setUp(self):
#         """Create user, auth headers, sample video, and URL helper."""
#         self.user = User.objects.create_user(username="u", password="p")
#         token = AccessToken.for_user(self.user)
#         self.auth = {"HTTP_AUTHORIZATION": f"Bearer {str(token)}"}

#         self.video = Video.objects.create(title="Dog", description="test")
#         self.res = "480p"

#         self.url = lambda vid, res, seg: reverse(
#             "video-segment", args=[vid, res, seg]
#         )

#     def _write_segment(self, video_id: int, resolution: str, segment_name: str, content: bytes = b"TS"):
#         """
#         Create directories and a dummy .ts segment file in MEDIA_ROOT.

#         Returns:
#         Path: Absolute path to the created segment file.
#         """
#         seg_rel_dir = Path("hls") / str(video_id) / resolution
#         seg_abs_dir = Path(settings.MEDIA_ROOT) / seg_rel_dir
#         seg_abs_dir.mkdir(parents=True, exist_ok=True)
#         seg_abs_path = seg_abs_dir / segment_name
#         seg_abs_path.write_bytes(content)
#         return seg_abs_path

#     # --- Tests ---

#     def test_unauthenticated_returns_401(self):
#         """401 Unauthorized: Request without auth token is rejected."""
#         url = self.url(self.video.id, self.res, "segment_00000.ts")
#         resp = self.client.get(url)
#         self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

#     def test_invalid_resolution_returns_404(self):
#         """404 Not Found: Invalid resolution results in error."""
#         url = self.url(self.video.id, "999p", "segment_00000.ts")
#         resp = self.client.get(url, **self.auth)
#         self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

#     def test_invalid_segment_name_returns_404(self):
#         """404 Not Found: Segment name fails regex validation."""
#         url = self.url(self.video.id, "720p", "bad/segment-name.ts")
#         self.client.cookies["access_token"] = self.token
#         resp = self.client.get(url)
#         self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

#     def test_variant_not_found_returns_404(self):
#         """404 Not Found: No variant exists for given video and resolution."""
#         url = self.url(self.video.id, self.res, "segment_00000.ts")
#         resp = self.client.get(url, **self.auth)
#         self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

#     def test_segment_missing_on_disk_returns_404(self):
#         """404 Not Found: Variant exists in DB, but segment file is missing on disk."""
#         VideoStreamVariant.objects.create(
#             video=self.video,
#             resolution=self.res,
#             manifest_path=f"hls/{self.video.id}/{self.res}/index.m3u8",
#         )
#         url = self.url(self.video.id, self.res, "segment_00042.ts")
#         resp = self.client.get(url, **self.auth)
#         self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

#     def test_serves_segment_with_correct_content_type_and_body(self):
#         """200 OK: Returns .ts segment file with correct content type and body."""
#         VideoStreamVariant.objects.create(
#             video=self.video,
#             resolution=self.res,
#             manifest_path=f"hls/{self.video.id}/{self.res}/index.m3u8",
#         )
#         body = b"\x00\x00\x01\xbaTS"
#         self._write_segment(self.video.id, self.res, "segment_00000.ts", body)

#         url = self.url(self.video.id, self.res, "segment_00000.ts")
#         resp = self.client.get(url, **self.auth)

#         self.assertEqual(resp.status_code, status.HTTP_200_OK)
#         self.assertEqual(resp["Content-Type"], "video/MP2T")
#         data = b"".join(resp.streaming_content)
#         self.assertEqual(data, body)
