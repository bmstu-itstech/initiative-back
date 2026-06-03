from django.apps import AppConfig


class MembersConfig(AppConfig):
    """Конфигурация приложения Members."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'server.apps.members'
    verbose_name = 'Members'
