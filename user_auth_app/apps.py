from django.apps import AppConfig


class UserAuthAppConfig(AppConfig):
    """
    Application configuration for the user_auth_app.

    The ready() method ensures that signal handlers are imported
    when the app is loaded.
    """
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'user_auth_app'

    def ready(self):
        import user_auth_app.signals
