from datetime import UTC, datetime

import msgspec
import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from server.apps.events.infra.mappers import (
    EventListMapper,
    EventMapper,
    MemberEventMapper,
)
from server.apps.events.infra.repository import EventRepo
from server.apps.events.logic.queries import EventFilterQuery, EventListQuery
from server.apps.events.logic.value_objects import EventIn
from server.apps.events.models import Event, EventOrganizer
from server.apps.members.models import Member


@pytest.fixture
def populated_event(member: Member) -> Event:
    """Готовит мероприятие с десятью ролями для проверки числа запросов."""  # noqa: RUF002
    start = datetime(2026, 10, 28, tzinfo=UTC)
    event = Event.objects.create(name='Встреча', starts_at=start, ends_at=start)
    EventOrganizer.objects.bulk_create([
        EventOrganizer(event=event, member=member, role=f'Роль {index}')
        for index in range(10)
    ])
    return event


@pytest.mark.django_db
def test_card_query_count(populated_event: Event) -> None:
    """Полная карточка загружается двумя запросами независимо от числа ролей."""
    repository = EventRepo()
    with CaptureQueriesContext(connection) as queries:
        card = EventMapper()(
            repository.get_by_id(populated_event.pk),
            repository.get_organizers(populated_event.pk),
        )
    assert (len(card.organizers), len(queries)) == (10, 2)


@pytest.mark.django_db
def test_membership_query_count(populated_event: Event, member: Member) -> None:
    """Членства с мероприятиями загружаются двумя запросами."""  # noqa: RUF002
    with CaptureQueriesContext(connection) as queries:
        rows = [
            MemberEventMapper(EventListMapper())(entry)
            for entry in EventRepo().get_memberships(
                member.pk,
                EventListQuery(),
            )
        ]
    assert (len(rows), len(queries)) == (10, 2)


@pytest.mark.django_db
def test_list_query_count(populated_event: Event) -> None:
    """Список мероприятий загружается одним запросом."""
    with CaptureQueriesContext(connection) as queries:
        listed = [
            EventListMapper()(entry)
            for entry in EventRepo().get_list(EventFilterQuery())
        ]
    assert (listed[0].name, len(queries)) == (populated_event.name, 1)


def test_event_date_order_validation() -> None:
    """DTO запрещает обратный интервал ещё до обращения к БД."""
    with pytest.raises(msgspec.ValidationError, match='Начало'):
        msgspec.convert(
            {
                'name': 'Встреча',
                'starts_at': '2026-10-29T10:00:00Z',
                'ends_at': '2026-10-28T10:00:00Z',
            },
            type=EventIn,
        )
