import csv
import io
import json

import pytest
from django.test import Client

from server.apps.events.models import Event
from server.apps.members.models import Member

JSON_MIME = 'application/json'
EVENTS_URL = '/api/events/'
CSV_ENCODING = 'utf-8-sig'
ID_KEY = 'id'
NAME_KEY = 'name'
DESCRIPTION_KEY = 'description'
LOCATIONS_KEY = 'locations'
NUL_CHARACTER = '\x00'


@pytest.mark.django_db
def test_event_not_found(
    editor_client: Client,
    event_payload: dict[str, object],
) -> None:
    """Карточка, обновление и экспорт отсутствующего объекта дают 404."""
    url = '/api/events/2147483647/'
    assert (
        editor_client.get(url).status_code,
        editor_client.put(
            url,
            event_payload,
            content_type=JSON_MIME,
        ).status_code,
        editor_client.get(f'{url}organizers/export/').status_code,
        editor_client.get('/api/members/2147483647/events/').status_code,
    ) == (
        404,
        404,
        404,
        404,
    )


@pytest.mark.django_db
def test_event_csv_exports(
    editor_client: Client,
    event_payload: dict[str, object],
    member: Member,
) -> None:
    """CSV сохраняет Unicode, списки мест и назначения без потери ролей."""
    created = editor_client.post(
        EVENTS_URL,
        event_payload,
        content_type=JSON_MIME,
    ).json()
    response = editor_client.get('/api/events/export/', HTTP_ACCEPT='text/html')
    rows = list(
        csv.DictReader(
            io.StringIO(response.content.decode(CSV_ENCODING)),
            delimiter=';',
        ),
    )
    assert (
        list(rows[0]),
        rows[0][DESCRIPTION_KEY],
        json.loads(rows[0][LOCATIONS_KEY]),
    ) == (
        [
            ID_KEY,
            NAME_KEY,
            'starts_at',
            'ends_at',
            DESCRIPTION_KEY,
            LOCATIONS_KEY,
        ],
        'Встреча; «ИУ»\nПрограмма',  # noqa: RUF001
        ['Аудитория; 1', 'Площадь «ИУ»'],
    )
    url = f'/api/events/{created[ID_KEY]}/organizers/export/'
    response = editor_client.get(url)
    assert response.status_code == 200
    rows = list(
        csv.DictReader(
            io.StringIO(response.content.decode(CSV_ENCODING)),
            delimiter=';',
        ),
    )
    assert rows == [
        {
            ID_KEY: str(member.pk),
            'full_name': str(member),
            'group': member.group,
            'role': 'Ведущий',
        },
    ]
    member.delete()
    response = editor_client.get(url)
    assert (
        response.content.decode(CSV_ENCODING) == 'id;full_name;group;role\r\n'
    )
    editor_client.delete(f'/api/events/{created[ID_KEY]}/')
    assert (
        editor_client.get(url).status_code,
        editor_client.get('/api/events/export/').content.decode(CSV_ENCODING),
    ) == (
        404,
        'id;name;starts_at;ends_at;description;locations\r\n',
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    'url',
    [
        EVENTS_URL,
        '/api/events/1/',
        '/api/events/export/',
        '/api/events/1/organizers/export/',
        '/api/members/1/events/',
    ],
)
def test_event_auth_required(client: Client, url: str) -> None:
    """Защищает каждый новый маршрут JWT-аутентификацией."""
    assert client.get(url).status_code == 401


@pytest.mark.django_db
@pytest.mark.parametrize(
    ('method', 'url'),
    [
        ('post', EVENTS_URL),
        ('put', '/api/events/1/'),
        ('delete', '/api/events/1/'),
    ],
)
def test_event_viewer_cannot_modify(
    viewer_client: Client,
    event_payload: dict[str, object],
    method: str,
    url: str,
) -> None:
    """Наблюдатель не может менять мероприятия."""
    response = viewer_client.generic(
        method.upper(),
        url,
        data=json.dumps(event_payload),
        content_type=JSON_MIME,
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_event_empty_defaults(editor_client: Client) -> None:
    """Допускает пустые списки и описание при равных датах."""
    response = editor_client.post(
        EVENTS_URL,
        {
            NAME_KEY: 'Встреча',
            'starts_at': '2026-10-28T10:00:00Z',
            'ends_at': '2026-10-28T10:00:00Z',
        },
        content_type=JSON_MIME,
    )
    assert response.status_code == 201
    card = response.json()
    assert (
        card[LOCATIONS_KEY],
        card['organizers'],
        bool(not card[DESCRIPTION_KEY]),
    ) == (
        [],
        [],
        True,
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    'field',
    [NAME_KEY, DESCRIPTION_KEY, LOCATIONS_KEY, 'organizers'],
)
def test_event_rejects_nul(
    editor_client: Client,
    event_payload: dict[str, object],
    member: Member,
    field: str,
) -> None:
    """Нулевой символ отклоняется до передачи строк драйверу БД."""
    query_parameters: dict[str, object] = {
        NAME_KEY: NUL_CHARACTER,
        DESCRIPTION_KEY: NUL_CHARACTER,
        LOCATIONS_KEY: [NUL_CHARACTER],
        'organizers': [{'member_id': member.pk, 'role': NUL_CHARACTER}],
    }
    event_payload[field] = query_parameters[field]
    response = editor_client.post(
        EVENTS_URL,
        event_payload,
        content_type=JSON_MIME,
    )
    assert (
        response.status_code,
        bool(not Event.objects.exists()),
    ) == (
        400,
        True,
    )
