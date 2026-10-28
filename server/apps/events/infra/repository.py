from typing import final

import attrs
from django.db import IntegrityError, transaction

from server.apps.events.infra.organizers import replace_organizers
from server.apps.events.infra.read_repository import EventReadRepo
from server.apps.events.logic.exceptions import (
    ObjectAlreadyExistsError,
    ObjectNotFoundError,
)
from server.apps.events.logic.value_objects import EventIn
from server.apps.events.models import Event


def _locked_event(event_id: int) -> Event:
    """Получает активное мероприятие под блокировкой строки."""
    try:
        return Event.objects.select_for_update().get(pk=event_id)
    except Event.DoesNotExist:
        raise ObjectNotFoundError('Мероприятие не найдено.') from None


@final
@attrs.define(slots=True, frozen=True)
class EventRepo(EventReadRepo):
    """Выполняет атомарные изменения мероприятий и оргкомитета."""

    def create(self, event_input: EventIn) -> Event:
        """Создаёт мероприятие и назначения одной транзакцией."""
        try:
            with transaction.atomic():
                event = Event.objects.create(
                    name=event_input.name,
                    starts_at=event_input.starts_at,
                    ends_at=event_input.ends_at,
                    description=event_input.description,
                    locations=event_input.locations,
                )
                replace_organizers(event.pk, event_input.organizers)
        except IntegrityError:
            raise ObjectAlreadyExistsError(
                'Нарушение целостности данных мероприятия.',
            ) from None
        return self.get_by_id(event.pk)

    def update(self, event_id: int, event_input: EventIn) -> Event:
        """Полностью заменяет мероприятие и оргкомитет под блокировкой."""
        try:
            with transaction.atomic():
                event = _locked_event(event_id)
                event.name = event_input.name
                event.starts_at = event_input.starts_at
                event.ends_at = event_input.ends_at
                event.description = event_input.description
                event.locations = event_input.locations
                event.save()
                replace_organizers(event.pk, event_input.organizers)
        except IntegrityError:
            raise ObjectAlreadyExistsError(
                'Нарушение целостности данных мероприятия.',
            ) from None
        return self.get_by_id(event_id)

    def delete(self, event_id: int) -> None:
        """Мягко удаляет мероприятие, сохраняя назначения."""
        try:
            event = Event.objects.get(pk=event_id)
        except Event.DoesNotExist:
            return
        event.delete()
