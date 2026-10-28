import csv
import io
from datetime import UTC, datetime

import pytest
from django.test import Client

from server.apps.members.models import Member

JSON_MIME = 'application/json'


@pytest.mark.django_db
def test_event_rejects_nul_search(viewer_client: Client) -> None:
    """Поисковый параметр проверяется до выполнения SQL."""
    assert viewer_client.get('/api/events/?search=%00').status_code == 400


@pytest.mark.django_db
def test_event_csv_formula_escaping(
    editor_client: Client,
    event_payload: dict[str, object],
    member: Member,
) -> None:
    """Экспорт экранирует формулы, сохраняя обычные значения."""
    event_payload.update({
        'name': '=1+1',
        'description': '@SUM(1)',
        'organizers': [{'member_id': member.pk, 'role': '+1+1'}],
    })
    created = editor_client.post(
        '/api/events/',
        event_payload,
        content_type=JSON_MIME,
    ).json()
    response = editor_client.get('/api/events/export/')
    rows = list(
        csv.DictReader(
            io.StringIO(response.content.decode('utf-8-sig')),
            delimiter=';',
        ),
    )
    assert (
        rows[0]['name'],
        rows[0]['description'],
    ) == (
        "'=1+1",
        "'@SUM(1)",
    )
    response = editor_client.get(
        f'/api/events/{created["id"]}/organizers/export/',
    )
    rows = list(
        csv.DictReader(
            io.StringIO(response.content.decode('utf-8-sig')),
            delimiter=';',
        ),
    )
    assert (
        rows[0]['role'],
        rows[0]['full_name'],
    ) == (
        "'+1+1",
        str(member),
    )


@pytest.mark.django_db
def test_event_invalid_route_returns_not_found(client: Client) -> None:
    """Ошибочный параметр маршрута документирован как ответ 404."""
    assert client.delete('/api/events/null%2Cnull/').status_code == 404


@pytest.mark.django_db
def test_event_superuser_can_create(
    client: Client,
    event_payload: dict[str, object],
    auth_headers_superuser: dict[str, str],
) -> None:
    """Суперпользователь создаёт мероприятие без членства в группах."""
    response = client.post(
        '/api/events/',
        event_payload,
        content_type=JSON_MIME,
        HTTP_AUTHORIZATION=auth_headers_superuser['HTTP_AUTHORIZATION'],
    )
    assert response.status_code == 201


@pytest.mark.django_db
def test_event_timezone_roundtrip(
    editor_client: Client,
    event_payload: dict[str, object],
) -> None:
    """Запись дат другого пояса возвращает ту же карточку, что чтение."""
    event_payload.update({
        'starts_at': '2026-10-28T13:00:00+03:00',
        'ends_at': '2026-10-28T15:00:00+03:00',
    })
    response = editor_client.post(
        '/api/events/',
        event_payload,
        content_type=JSON_MIME,
    )
    assert response.status_code == 201
    created = response.json()
    url = f'/api/events/{created["id"]}/'
    assert (
        created,
        datetime.fromisoformat(created['starts_at']),
    ) == (
        editor_client.get(url).json(),
        datetime(2026, 10, 28, 10, tzinfo=UTC),
    )
    event_payload['name'] = 'Обновлённое название'
    response = editor_client.put(
        url,
        event_payload,
        content_type=JSON_MIME,
    )
    assert (
        response.status_code,
        response.json(),
    ) == (
        200,
        editor_client.get(url).json(),
    )
