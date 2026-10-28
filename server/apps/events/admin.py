from typing import override

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest

from server.apps.events.models import Event, EventOrganizer


@admin.register(Event)
class EventAdmin(admin.ModelAdmin[Event]):
    """Администрирование мероприятий без физического удаления."""

    list_display = ('id', 'name', 'starts_at', 'ends_at', 'deleted_at')
    list_filter = ('deleted_at',)
    search_fields = ('name',)

    @override
    def get_queryset(  # noqa: WPS615 — имя метода задано Django
        self,
        request: HttpRequest,
    ) -> QuerySet[Event]:
        """Показывает также мягко удалённые мероприятия."""
        queryset: QuerySet[Event] = Event.all_objects.all()
        return queryset

    @override
    def delete_model(self, request: HttpRequest, event: Event) -> None:
        """Мягко удаляет выбранное мероприятие."""
        event.delete()

    @override
    def delete_queryset(
        self,
        request: HttpRequest,
        queryset: QuerySet[Event],
    ) -> None:
        """Сохраняет мягкое удаление при массовой операции."""
        for event in queryset:
            event.delete()


@admin.register(EventOrganizer)
class EventOrganizerAdmin(admin.ModelAdmin[EventOrganizer]):
    """Администрирование назначений в оргкомитеты."""

    list_display = ('id', 'event', 'member', 'role')
    search_fields = ('event__name', 'member__last_name', 'role')
    list_select_related = ('event', 'member')
