from unittest.mock import patch

import msgspec
import pytest
from django.db import (
    connection,
)
from django.test.utils import CaptureQueriesContext

from server.apps.events.infra import mappers
from server.apps.events.infra.repository import EventRepo
from server.apps.events.logic.value_objects import EventIn, EventOrganizerIn
from server.apps.events.models import EventOrganizer
from server.apps.members.models import Member

HOST_ROLE = 'Ведущий'


@pytest.mark.django_db
def test_unchanged_organizers_are_not_recreated(event_data: EventIn) -> None:
    """Обновление названия не пересоздаёт неизменившиеся назначения."""
    repository = EventRepo()
    event = repository.create(event_data)
    original_id = EventOrganizer.objects.get(event_id=event.pk).pk
    event_data.name = 'Новое название'
    with CaptureQueriesContext(connection) as queries:
        updated = repository.update(event.pk, event_data)
    assert (
        updated.name,
        EventOrganizer.objects.get(event_id=event.pk).pk,
        bool(
            not any(
                query['sql'].startswith(('DELETE', 'INSERT'))
                for query in queries
            ),
        ),
    ) == (
        'Новое название',
        original_id,
        True,
    )


@pytest.mark.django_db
def test_organizer_diff_preserves_assignments(
    event_data: EventIn,
    member: Member,
) -> None:
    """Синхронизация сохраняет общие роли и изменяет только разницу."""
    repository = EventRepo()
    event_data.organizers.append(
        EventOrganizerIn(member_id=member.pk, role='Устаревшая роль'),
    )
    event = repository.create(event_data)
    another = repository.create(event_data)
    original = EventOrganizer.objects.get(event_id=event.pk, role=HOST_ROLE)
    event_data.organizers = [
        EventOrganizerIn(member_id=member.pk, role=HOST_ROLE),
        EventOrganizerIn(member_id=member.pk, role='Новая роль'),
    ]
    repository.update(event.pk, event_data)
    assert (
        EventOrganizer.objects.get(event_id=event.pk, role=HOST_ROLE).pk,
        set(
            EventOrganizer.objects.filter(event_id=event.pk).values_list(
                'role',
                flat=True,
            ),
        ),
        set(
            EventOrganizer.objects.filter(event_id=another.pk).values_list(
                'role',
                flat=True,
            ),
        ),
    ) == (
        original.pk,
        {HOST_ROLE, 'Новая роль'},
        {HOST_ROLE, 'Устаревшая роль'},
    )


@pytest.mark.django_db
@pytest.mark.parametrize('optional_fields', ['', 'Заполнено'])
def test_organizer_projection(
    event_data: EventIn,
    member: Member,
    optional_fields: str,
) -> None:
    """Проекции формируют прежний ответ без создания ORM-моделей."""
    member.patronymic = optional_fields
    member.group = optional_fields
    member.save(update_fields=['patronymic', 'group'])
    repository = EventRepo()
    event = repository.create(event_data)
    with (
        patch.object(Member, 'from_db', side_effect=AssertionError),
        patch.object(EventOrganizer, 'from_db', side_effect=AssertionError),
    ):
        with CaptureQueriesContext(connection) as queries:
            card = mappers.EventMapper()(
                repository.get_by_id(event.pk),
                repository.get_organizers(event.pk),
            )
        export_record = repository.get_organizers_for_export(event.pk)[0]
    assert (
        len(queries),
        card.organizers[0].member.id,
        card.organizers[0].member.patronymic,
        card.organizers[0].member.group,
        card.organizers[0].role,
        bool(msgspec.json.encode(card)),
        export_record.member_id,
        mappers.EventOrganizerExportMapper()(export_record).full_name,
    ) == (
        2,
        member.pk,
        optional_fields or None,
        optional_fields or None,
        HOST_ROLE,
        True,
        member.pk,
        str(member),
    )
