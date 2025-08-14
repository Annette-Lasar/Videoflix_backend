from django.urls import path
from .views import (VideoListView,
                    video_variant_manifest, 
                    video_segment)

urlpatterns = [
    path("video/", VideoListView.as_view(), name="video-list"),
    path(
        "video/<int:movie_id>/<str:resolution>/index.m3u8",
        video_variant_manifest,
        name="video-variant-manifest",
    ),
    path(
        "video/<int:movie_id>/<str:resolution>/<str:segment>",
        video_segment,
        name="video-segment",
    ),
]
