from django.apps import AppConfig


class VideoAppConfig(AppConfig):
    """
    The ready() method ensures that signal handlers are imported
    when the app is loaded.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'video_app'

    def ready(self):
        import video_app.signals
