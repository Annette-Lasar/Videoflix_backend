from django.contrib import admin
from .models import Video, VideoStreamVariant, UserWatchProgress


class VideoStreamVariantInline(admin.TabularInline):
    model = VideoStreamVariant
    extra = 1
    exclude = ('manifest_path',)


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "processing_status", "processing_progress", "duration_seconds", "file_size_mb", "created_at")
    list_filter = ("title", "category", "processing_status", "created_at")
    search_fields = ("title", "description")
    ordering = ("-created_at",)
    inlines = [VideoStreamVariantInline]

    def available_resolutions(self, obj):
        return ", ".join(
            variant.resolution for variant in obj.variants.all()
        )
    available_resolutions.short_description = "Resolutions"


@admin.register(UserWatchProgress)
class UserWatchProgressAdmin(admin.ModelAdmin):
    list_display = ("user", "video", "resolution",
                    "last_position_seconds", "updated_at")
    list_filter = ("resolution", "updated_at")
    search_fields = ("user__username", "video__title")
    ordering = ("-updated_at",)
