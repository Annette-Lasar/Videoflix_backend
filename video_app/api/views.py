import logging
import re
from pathlib import Path
from django.conf import settings
from django.http import FileResponse, Http404
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from core.settings import MEDIA_ROOT
from rest_framework.response import Response
from rest_framework import status
from ..models import Video, VideoStreamVariant
from utils.data import RESOLUTION_CHOICES
logger = logging.getLogger(__name__)


ALLOWED_RESOLUTIONS = {
    (c[0] if isinstance(c, (list, tuple)) else c) for c in RESOLUTION_CHOICES
}

SEGMENT_NAME_RE = re.compile(r"^segment_\d{5}\.ts$")


class VideoListView(APIView):
    """
    Returns a list of videos ordered by newest first.

    Each item includes id, created_at, title, description, category,
    and an absolute thumbnail URL if available.
    """

    def get(self, request):
        try:
            videos = Video.objects.all().order_by("-created_at")
            data = [
                {
                    "id": v.id,
                    "created_at": v.created_at,
                    "title": v.title,
                    "description": v.description,
                    "category": v.category,
                    "thumbnail_url": f"{settings.BASE_BACKEND_URL}{settings.MEDIA_URL}{v.thumbnail_url}" if v.thumbnail_url else None
                }
                for v in videos
            ]
            return Response(data, status=status.HTTP_200_OK)
        except Exception:
            logger.exception("Failed to list videos")
            return Response(
                {"detail": "Internal server error."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@api_view(["GET"])
def video_variant_manifest(request, movie_id: int, resolution: str):
    """
    Return the HLS manifest (.m3u8) file for a given video and resolution.

    Args:
        movie_id (int): ID of the video.
        resolution (str): Target resolution (must be in ALLOWED_RESOLUTIONS).

    Raises:
        Http404: If the resolution is invalid, the variant does not exist,
                 or the manifest file cannot be found.

    Returns:
        FileResponse: The requested HLS manifest file with 
        content type 'application/vnd.apple.mpegurl'.
    """
    if resolution not in ALLOWED_RESOLUTIONS:
        raise Http404("Invalid resolution")

    try:
        variant = VideoStreamVariant.objects.get(
            video_id=movie_id,
            resolution=resolution
        )
    except VideoStreamVariant.DoesNotExist:
        raise Http404("Variant not found")

    manifest_path = Path(variant.manifest_path)
    if not manifest_path.is_absolute():
        manifest_path = Path(settings.MEDIA_ROOT) / manifest_path

    if not manifest_path.exists():
        raise Http404("Manifest file not found")

    return FileResponse(open(manifest_path, "rb"), content_type="application/vnd.apple.mpegurl")


@api_view(["GET"])
def video_segment(request, movie_id: int, resolution: str, segment: str):
    """
    Return a single HLS video segment (.ts file) for the given video and resolution.

    Args:
        movie_id (int): ID of the video.
        resolution (str): Target resolution (must be in ALLOWED_RESOLUTIONS).
        segment (str): Filename of the segment (validated against SEGMENT_NAME_RE).

    Raises:
        Http404: If the resolution is invalid, the segment name is invalid,
                 the variant does not exist, or the segment file cannot be found.

    Returns:
        FileResponse: The requested video segment with 
        content type 'video/MP2T'.
    """
    if resolution not in ALLOWED_RESOLUTIONS:
        raise Http404("Invalid resolution")

    if not SEGMENT_NAME_RE.match(segment):
        raise Http404("Invalid segment name")

    get_object_or_404(VideoStreamVariant, video_id=movie_id,
                      resolution=resolution)

    seg_path = Path(settings.MEDIA_ROOT) / "hls" / \
        str(movie_id) / resolution / segment
    if not seg_path.exists():
        raise Http404("Segment not found")

    return FileResponse(seg_path.open("rb"), content_type="video/MP2T")
