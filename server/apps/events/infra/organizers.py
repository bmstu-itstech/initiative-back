import attrs

from server.apps.events.logic.exceptions import (
    EventValidationError,
    ObjectAlreadyExistsError,
)
from server.apps.events.logic.value_objects import EventOrganizerIn
from server.apps.events.models import EventOrganizer
from server.apps.members.models import Member


@attrs.define(slots=True, frozen=True)
class OrganizerChanges:
    """Подготовленные изменения до захвата блокировок активистов."""

    additions: list[EventOrganizer]
    obsolete_ids: list[int]
    existing_count: int


def _prepare_changes(
    event_id: int,
    organizers: list[EventOrganizerIn],
) -> OrganizerChanges:
    """Проверяет дубликаты и готовит только изменившиеся назначения."""
    incoming = {
        (organizer.member_id, organizer.role) for organizer in organizers
    }
    if len(incoming) != len(organizers):
        raise ObjectAlreadyExistsError(
            'Нарушение целостности данных мероприятия.',
        )
    existing = _existing_assignments(event_id)
    return OrganizerChanges(
        additions=[
            EventOrganizer(
                event_id=event_id,
                member_id=organizer.member_id,
                role=organizer.role,
            )
            for organizer in organizers
            if (organizer.member_id, organizer.role) not in existing
        ],
        obsolete_ids=[
            primary_key
            for assignment, primary_key in existing.items()
            if assignment not in incoming
        ],
        existing_count=len(existing),
    )


def _lock_members(organizers: list[EventOrganizerIn]) -> None:
    """Блокирует активных участников в общем порядке и проверяет их наличие."""
    member_ids = {organizer.member_id for organizer in organizers}
    active_ids = set(
        Member.objects
        .select_for_update()
        .filter(pk__in=member_ids)
        .order_by('pk')
        .values_list('pk', flat=True),
    )
    if active_ids != member_ids:
        raise EventValidationError('Указан несуществующий активист.')


def replace_organizers(
    event_id: int,
    organizers: list[EventOrganizerIn],
) -> None:
    """Синхронизирует назначения в транзакции вызывающего репозитория."""
    changes = _prepare_changes(event_id, organizers)
    _lock_members(organizers)
    if changes.obsolete_ids:
        obsolete = EventOrganizer.objects.filter(event_id=event_id)
        if len(changes.obsolete_ids) != changes.existing_count:
            obsolete = obsolete.filter(pk__in=changes.obsolete_ids)
        obsolete.delete()
    EventOrganizer.objects.bulk_create(changes.additions)


def _existing_assignments(event_id: int) -> dict[tuple[int, str], int]:
    """Читает ключи существующих назначений без загрузки моделей."""
    return {
        (member_id, role): primary_key
        for primary_key, member_id, role in EventOrganizer.objects.filter(
            event_id=event_id,
        ).values_list('pk', 'member_id', 'role')
    }
