from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        # Import signals so they get registered when Django starts
        try:
            from . import signals  # noqa: F401
        except Exception:
            # Avoid breaking startup if migrations are running and models aren't ready
            pass
