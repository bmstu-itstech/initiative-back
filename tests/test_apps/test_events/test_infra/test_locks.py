from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from threading import Barrier
from unittest.mock import patch

import attrs
import pytest
from django.db import close_old_connections, connections, transaction

from server.apps.events.infra.repository import EventRepo
from server.apps.events.logic.value_objects import EventIn, EventOrganizerIn
from server.apps.events.models import EventOrganizer
from server.apps.members.models import Member


def _lock_member(member_id: int) -> None:
    """Проверяет доступность строки из независимого соединения."""
    close_old_connections()
    with closing(connections['default']), transaction.atomic():
        Member.objects.select_for_update(nowait=True).get(pk=member_id)


@attrs.define(slots=True, frozen=True)
class AssignmentProbe:
    """Проверяет отсутствие блокировки участника при создании ORM-объекта."""

    member_id: int
    pool: ThreadPoolExecutor
    original_init: Callable[..., None]

    def __call__(
        self,
        organizer: EventOrganizer,
        *args: object,
        **kwargs: object,
    ) -> None:
        """Создаёт назначение и пробует заблокировать активиста извне."""
        self.original_init(organizer, *args, **kwargs)
        self.pool.submit(_lock_member, self.member_id).result(timeout=1)


@pytest.mark.django_db(transaction=True)
def test_prepare_before_member_locks(
    event_data: EventIn,
    member: Member,
) -> None:
    """Подготовка объектов не удерживает блокировки общих участников."""
    event = EventRepo().create(event_data)
    event_data.organizers.append(
        EventOrganizerIn(member_id=member.pk, role='Новая роль'),
    )
    with (
        ThreadPoolExecutor(max_workers=1) as pool,
        patch.object(
            EventOrganizer,
            '__init__',
            autospec=True,
            side_effect=AssignmentProbe(
                member.pk,
                pool,
                EventOrganizer.__init__,
            ),
        ),
    ):
        EventRepo().update(event.pk, event_data)
    assert EventOrganizer.objects.filter(event_id=event.pk).count() == 2


def _concurrent_update(
    event_id: int,
    event_input: EventIn,
    barrier: Barrier,
) -> None:
    """Одновременно обновляет мероприятие через отдельное соединение."""
    close_old_connections()
    with closing(connections['default']):
        barrier.wait(timeout=3)
        EventRepo().update(event_id, event_input)


@pytest.mark.django_db(transaction=True)
def test_concurrent_updates_are_atomic(
    event_data: EventIn,
    member: Member,
) -> None:
    """Конкурентные PUT не смешивают два разных состава оргкомитета."""
    event = EventRepo().create(event_data)
    another = Member.objects.create(
        first_name='Пётр',
        last_name='Петров',
        telegram='concurrent',
    )
    _run_updates(event.pk, event_data, (member.pk, another.pk))
    event.refresh_from_db()
    assert list(
        EventOrganizer.objects
        .filter(event_id=event.pk)
        .order_by('member_id')
        .values_list('member_id', 'role'),
    ) == [(member.pk, event.name), (another.pk, event.name)]


def _run_updates(
    event_id: int,
    event_input: EventIn,
    member_ids: tuple[int, int],
) -> None:
    """Запускает два конкурирующих изменения и дожидается обоих."""
    barrier = Barrier(2)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [
            pool.submit(
                _concurrent_update,
                event_id,
                EventIn(
                    name=role,
                    starts_at=event_input.starts_at,
                    ends_at=event_input.ends_at,
                    organizers=[
                        EventOrganizerIn(member_id=activist_id, role=role)
                        for activist_id in (member_ids)
                    ],
                ),
                barrier,
            )
            for role in ('Первая роль', 'Вторая роль')
        ]
        for future in futures:
            future.result(timeout=3)
