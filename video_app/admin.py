from django.contrib import admin
from .models import Video, VideoStreamVariant, UserWatchProgress


class VideoStreamVariantInline(admin.TabularInline):
    """Inline admin configuration for video stream variants."""
    model = VideoStreamVariant
    extra = 1
    exclude = ('manifest_path',)


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    """Admin configuration for Video objects."""
    list_display = ("id", "title", "processing_status", "processing_progress",
                    "duration_seconds", "file_size_mb", "created_at")
    list_filter = ("title", "category", "processing_status", "created_at")
    search_fields = ("title", "description")
    ordering = ("-created_at",)
    inlines = [VideoStreamVariantInline]

    def available_resolutions(self, obj):
        """Return all available resolutions for a video as a comma-separated string."""
        return ", ".join(
            variant.resolution for variant in obj.variants.all()
        )
    available_resolutions.short_description = "Resolutions"


@admin.register(UserWatchProgress)
class UserWatchProgressAdmin(admin.ModelAdmin):
    """Admin configuration for user watch progress entries."""
    list_display = ("user", "video", "resolution",
                    "last_position_seconds", "updated_at")
    list_filter = ("resolution", "updated_at")
    search_fields = ("user__username", "video__title")
    ordering = ("-updated_at",)
