from django.contrib import admin
from .models import Video, VideoStreamVariant, UserWatchProgress


class VideoStreamVariantInline(admin.TabularInline):
    model = VideoStreamVariant
    extra = 1
    exclude = ('manifest_path',)


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "available_resolutions", "created_at")
    search_fields = ("title", "category")
    list_filter = ("category", "created_at")
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
