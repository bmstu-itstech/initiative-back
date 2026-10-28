from datetime import UTC, datetime, timedelta

import pytest
from django.test import Client

from server.apps.events.models import Event, EventOrganizer
from server.apps.members.models import Member


@pytest.fixture
def editor_client(
    client: Client,
    auth_headers_editor: dict[str, str],
) -> Client:
    """Возвращает HTTP-клиент редактора."""
    client.defaults.update(auth_headers_editor)
    return client


@pytest.fixture
def viewer_client(
    auth_headers_viewer: dict[str, str],
) -> Client:
    """Возвращает HTTP-клиент наблюдателя."""
    return Client(HTTP_AUTHORIZATION=auth_headers_viewer['HTTP_AUTHORIZATION'])


@pytest.fixture
def event_payload(member: Member) -> dict[str, object]:
    """Готовит корректный запрос создания мероприятия."""
    return {
        'name': 'День факультета',
        'starts_at': '2026-10-28T10:00:00Z',
        'ends_at': '2026-10-28T12:00:00Z',
        'description': 'Встреча; «ИУ»\nПрограмма',  # noqa: RUF001
        'locations': ['Аудитория; 1', 'Площадь «ИУ»'],
        'organizers': [{'member_id': member.pk, 'role': 'Ведущий'}],
    }


@pytest.fixture
def scheduled_events(member: Member) -> tuple[Event, Event]:
    """Создаёт два события с разными датами и несколькими ролями."""  # noqa: RUF002
    start = datetime(2026, 10, 28, 10, tzinfo=UTC)
    first = Event.objects.create(
        name='День факультета',
        starts_at=start,
        ends_at=start,
    )
    second = Event.objects.create(
        name='Спортивный турнир',
        starts_at=start + timedelta(days=1),
        ends_at=start + timedelta(days=1),
    )
    EventOrganizer.objects.bulk_create([
        EventOrganizer(event=first, member=member, role='Ведущий'),
        EventOrganizer(event=second, member=member, role='Ведущий'),
        EventOrganizer(event=second, member=member, role='Организатор'),
    ])
    return first, second
