from django.apps import AppConfig


class AuthConfig(AppConfig):
    """Конфигурация приложения Auth."""

    name = 'server.apps.auth'
    label = 'custom_auth'
    verbose_name = 'Auth and roles'
