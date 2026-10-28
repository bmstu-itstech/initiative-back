from django.apps import AppConfig


class EventsConfig(AppConfig):
    """Конфигурация приложения мероприятий."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'server.apps.events'
    verbose_name = 'Мероприятия'
