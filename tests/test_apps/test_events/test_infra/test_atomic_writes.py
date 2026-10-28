from datetime import timedelta

import pytest
from django.db import (
    connection,
)
from django.test.utils import CaptureQueriesContext

from server.apps.events.infra.repository import EventRepo
from server.apps.events.logic.exceptions import ObjectAlreadyExistsError
from server.apps.events.logic.value_objects import EventIn, EventOrganizerIn
from server.apps.events.models import Event, EventOrganizer
from server.apps.members.models import Member

HOST_ROLE = 'Ведущий'


@pytest.mark.django_db
@pytest.mark.parametrize('update', [False, True])
def test_database_constraint_failure_is_atomic(
    event_data: EventIn,
    *,
    update: bool,
) -> None:
    """Ошибка ограничения БД преобразуется без частичного сохранения."""
    repository = EventRepo()
    original = repository.create(event_data)
    event_data.name = 'Некорректный интервал'
    event_data.ends_at = event_data.starts_at - timedelta(seconds=1)
    if update:
        with pytest.raises(ObjectAlreadyExistsError):
            repository.update(original.pk, event_data)
    else:
        with pytest.raises(ObjectAlreadyExistsError):
            repository.create(event_data)
    assert (
        Event.objects.count(),
        repository.get_by_id(original.pk).name,
        EventOrganizer.objects.filter(event_id=original.pk).count(),
    ) == (
        1,
        'Встреча',
        1,
    )


@pytest.mark.django_db
def test_full_replacement_delete_filter(
    event_data: EventIn,
    member: Member,
) -> None:
    """Полная замена не передаёт все ID удаляемых назначений в SQL."""
    repository = EventRepo()
    event_data.organizers = [
        EventOrganizerIn(member_id=member.pk, role=f'Старая роль {index}')
        for index in range(20)
    ]
    event = repository.create(event_data)
    another = repository.create(event_data)
    event_data.organizers = [
        EventOrganizerIn(member_id=member.pk, role=f'Новая роль {index}')
        for index in range(20)
    ]
    with CaptureQueriesContext(connection) as queries:
        repository.update(event.pk, event_data)
        deletes = [
            statement['sql']
            for statement in queries
            if statement['sql'].startswith('DELETE')
        ]
    assert (
        len(deletes),
        bool(' IN ' not in deletes[0]),
        EventOrganizer.objects.filter(event_id=event.pk).count(),
        bool(
            not EventOrganizer.objects.filter(
                event_id=event.pk,
                role__startswith='Старая',
            ).exists(),
        ),
        EventOrganizer.objects.filter(event_id=another.pk).count(),
    ) == (
        1,
        True,
        20,
        True,
        20,
    )
