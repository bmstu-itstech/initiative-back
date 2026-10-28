from typing import final

import attrs

from server.apps.events.infra import mappers
from server.apps.events.infra.repository import EventRepo
from server.apps.events.logic.queries import EventFilterQuery, EventListQuery
from server.apps.events.logic.value_objects import (
    EventIn,
    EventListOut,
    EventOut,
    MemberEventOut,
)
from server.common.value_objects import SuccessResponse


@final
@attrs.define(slots=True, frozen=True)
class GetEventList:
    """Получает страницу мероприятий без оргкомитета."""

    _repository: EventRepo
    _mapper: mappers.EventListMapper

    def __call__(self, query: EventFilterQuery) -> list[EventListOut]:
        """Возвращает отсортированную страницу мероприятий."""
        return [
            self._mapper(event) for event in self._repository.get_list(query)
        ]


@final
@attrs.define(slots=True, frozen=True)
class GetEvent:
    """Получает полную карточку мероприятия."""

    _repository: EventRepo
    _mapper: mappers.EventMapper

    def __call__(self, event_id: int) -> EventOut:
        """Возвращает мероприятие с оргкомитетом."""  # noqa: RUF002
        event = self._repository.get_by_id(event_id)
        return self._mapper(event, self._repository.get_organizers(event_id))


@final
@attrs.define(slots=True, frozen=True)
class CreateEvent:
    """Создаёт мероприятие с оргкомитетом."""  # noqa: RUF002

    _repository: EventRepo
    _mapper: mappers.EventMapper

    def __call__(self, event_input: EventIn) -> EventOut:
        """Возвращает созданную карточку."""
        event = self._repository.create(event_input)
        return self._mapper(event, self._repository.get_organizers(event.pk))


@final
@attrs.define(slots=True, frozen=True)
class UpdateEvent:
    """Полностью обновляет мероприятие с оргкомитетом."""  # noqa: RUF002

    _repository: EventRepo
    _mapper: mappers.EventMapper

    def __call__(self, event_id: int, event_input: EventIn) -> EventOut:
        """Возвращает обновлённую карточку."""
        event = self._repository.update(event_id, event_input)
        return self._mapper(event, self._repository.get_organizers(event_id))


@final
@attrs.define(slots=True, frozen=True)
class DeleteEvent:
    """Мягко удаляет мероприятие."""

    _repository: EventRepo

    def __call__(self, event_id: int) -> SuccessResponse:
        """Возвращает успешный ответ также при повторном удалении."""
        self._repository.delete(event_id)
        return SuccessResponse(status='success', message='Event deleted (soft)')


@final
@attrs.define(slots=True, frozen=True)
class GetMemberEvents:
    """Получает роли активиста с краткими мероприятиями."""  # noqa: RUF002

    _repository: EventRepo
    _mapper: mappers.MemberEventMapper

    def __call__(
        self,
        member_id: int,
        query: EventListQuery,
    ) -> list[MemberEventOut]:
        """Возвращает страницу назначений активиста."""
        return [
            self._mapper(organizer)
            for organizer in self._repository.get_memberships(member_id, query)
        ]
