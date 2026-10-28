import json
from typing import final

import attrs

from server.apps.events.infra.records import (
    OrganizerExportRecord,
    OrganizerRecord,
)
from server.apps.events.logic.export_rows import (
    EventExportRow,
    EventOrganizerExportRow,
)
from server.apps.events.logic.value_objects import (
    EventListOut,
    EventOrganizerOut,
    EventOut,
    MemberEventOut,
)
from server.apps.events.models import Event, EventOrganizer
from server.apps.members.logic.value_objects import MemberListOut


@final
@attrs.define(slots=True, frozen=True)
class EventListMapper:
    """Преобразует мероприятие без загрузки оргкомитета."""

    def __call__(self, event: Event) -> EventListOut:
        """Возвращает краткий DTO мероприятия."""
        return EventListOut(
            id=event.pk,
            name=event.name,
            starts_at=event.starts_at,
            ends_at=event.ends_at,
            description=event.description,
            locations=event.locations,
        )


@final
@attrs.define(slots=True, frozen=True)
class EventMapper:
    """Собирает полную карточку с данными активистов."""  # noqa: RUF002

    def __call__(
        self,
        event: Event,
        organizers: list[OrganizerRecord],
    ) -> EventOut:
        """Преобразует мероприятие и проекции оргкомитета в карточку."""
        return EventOut(
            id=event.pk,
            name=event.name,
            starts_at=event.starts_at,
            ends_at=event.ends_at,
            description=event.description,
            locations=event.locations,
            organizers=[
                EventOrganizerOut(
                    member=MemberListOut(
                        id=organizer.member_id,
                        first_name=organizer.first_name,
                        last_name=organizer.last_name,
                        patronymic=organizer.patronymic or None,
                        telegram=organizer.telegram,
                        group=organizer.group or None,
                        birth_date=organizer.birth_date,
                        join_date=organizer.join_date,
                    ),
                    role=organizer.role,
                )
                for organizer in organizers
            ],
        )


@final
@attrs.define(slots=True, frozen=True)
class MemberEventMapper:
    """Преобразует назначение в роль с кратким мероприятием."""  # noqa: RUF002

    _event_mapper: EventListMapper

    def __call__(self, organizer: EventOrganizer) -> MemberEventOut:
        """Возвращает членство без вложенного оргкомитета."""
        return MemberEventOut(
            event=self._event_mapper(organizer.event),
            role=organizer.role,
        )


@final
@attrs.define(slots=True, frozen=True)
class EventExportMapper:
    """Готовит строковые значения для CSV мероприятий."""

    def __call__(self, event: Event) -> EventExportRow:
        """Сериализует даты и список мест в CSV-ячейки."""
        return EventExportRow(
            id=event.pk,
            name=event.name,
            starts_at=event.starts_at.isoformat(),
            ends_at=event.ends_at.isoformat(),
            description=event.description,
            locations=json.dumps(event.locations, ensure_ascii=False),
        )


@final
@attrs.define(slots=True, frozen=True)
class EventOrganizerExportMapper:
    """Готовит строку CSV оргкомитета."""

    def __call__(
        self,
        organizer: OrganizerExportRecord,
    ) -> EventOrganizerExportRow:
        """Возвращает ID, ФИО, группу и роль активиста."""
        parts = [organizer.last_name, organizer.first_name]
        if organizer.patronymic:
            parts.append(organizer.patronymic)
        return EventOrganizerExportRow(
            id=organizer.member_id,
            full_name=' '.join(parts),
            group=organizer.group,
            role=organizer.role,
        )
