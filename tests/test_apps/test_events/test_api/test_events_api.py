import json

import pytest
from django.test import Client

from server.apps.events.models import Event, EventOrganizer
from server.apps.members.models import Member

NAME_KEY = 'name'
START_KEY = 'starts_at'
ORGANIZERS_KEY = 'organizers'
MEMBER_KEY = 'member_id'
ROLE_KEY = 'role'
ORGANIZER_ROLE = 'Организатор'
HOST_ROLE = 'Ведущий'
EVENTS_URL = '/api/events/'
JSON_MIME = 'application/json'
AUTH_HEADER = 'HTTP_AUTHORIZATION'
ID_KEY = 'id'
FILLER_CHARACTER = 'x'


@pytest.mark.django_db
def test_event_lifecycle(
    client: Client,
    member: Member,
    auth_headers_editor: dict[str, str],
    auth_headers_viewer: dict[str, str],
) -> None:
    """Создаёт мероприятие с несколькими ролями и мягко удаляет его."""  # noqa: RUF002
    payload = {
        NAME_KEY: 'День факультета',
        START_KEY: '2026-10-28T10:00:00Z',
        'ends_at': '2026-10-28T12:00:00Z',
        'locations': ['Аудитория 1', 'Аудитория 2'],
        ORGANIZERS_KEY: [
            {MEMBER_KEY: member.pk, ROLE_KEY: ORGANIZER_ROLE},
            {MEMBER_KEY: member.pk, ROLE_KEY: HOST_ROLE},
        ],
    }
    response = client.post(
        EVENTS_URL,
        payload,
        content_type=JSON_MIME,
        HTTP_AUTHORIZATION=auth_headers_editor[AUTH_HEADER],
    )
    assert response.status_code == 201
    event = response.json()
    assert (
        bool(not event['description']),
        {entry[ROLE_KEY] for entry in event[ORGANIZERS_KEY]},
        event[ORGANIZERS_KEY][0]['member'][ID_KEY],
    ) == (
        True,
        {ORGANIZER_ROLE, HOST_ROLE},
        member.pk,
    )
    url = f'/api/events/{event[ID_KEY]}/'
    assert (
        client.get(
            url,
            HTTP_AUTHORIZATION=auth_headers_viewer[AUTH_HEADER],
        ).json()
        == event
    )
    payload[ORGANIZERS_KEY] = []
    response = client.put(
        url,
        payload,
        content_type=JSON_MIME,
        HTTP_AUTHORIZATION=auth_headers_editor[AUTH_HEADER],
    )
    assert (
        response.status_code,
        response.json()[ORGANIZERS_KEY],
        client.delete(
            url,
            HTTP_AUTHORIZATION=auth_headers_editor[AUTH_HEADER],
        ).status_code,
        client.get(
            url,
            HTTP_AUTHORIZATION=auth_headers_viewer[AUTH_HEADER],
        ).status_code,
        client.delete(
            url,
            HTTP_AUTHORIZATION=auth_headers_editor[AUTH_HEADER],
        ).status_code,
    ) == (
        200,
        [],
        200,
        404,
        200,
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    ('changes', 'status'),
    [
        ({NAME_KEY: ''}, 400),
        ({NAME_KEY: FILLER_CHARACTER * 65}, 400),
        ({'description': FILLER_CHARACTER * 513}, 400),
        ({'description': None}, 400),
        ({'locations': [FILLER_CHARACTER * 65]}, 400),
        ({'locations': 'Аудитория'}, 400),
        ({START_KEY: '2026-10-29T10:00:00Z'}, 400),
        ({START_KEY: '2026-10-28T10:00:00'}, 400),
        ({ORGANIZERS_KEY: [{MEMBER_KEY: 0, ROLE_KEY: HOST_ROLE}]}, 400),
        (
            {ORGANIZERS_KEY: [{MEMBER_KEY: 2147483647, ROLE_KEY: HOST_ROLE}]},
            400,
        ),
        ({ORGANIZERS_KEY: [{MEMBER_KEY: 1, ROLE_KEY: ''}]}, 400),
        (
            {
                ORGANIZERS_KEY: [
                    {MEMBER_KEY: 1, ROLE_KEY: FILLER_CHARACTER * 65},
                ],
            },
            400,
        ),
    ],
)
def test_event_invalid_input(
    editor_client: Client,
    event_payload: dict[str, object],
    changes: dict[str, object],
    status: int,
) -> None:
    """Отклоняет некорректные поля без создания мероприятия."""
    event_payload.update(changes)
    response = editor_client.post(
        EVENTS_URL,
        event_payload,
        content_type=JSON_MIME,
    )
    assert (
        response.status_code,
        bool(not Event.objects.exists()),
    ) == (
        status,
        True,
    )


@pytest.mark.django_db
@pytest.mark.parametrize('update', [False, True])
def test_event_duplicate_organizers_rollback(
    editor_client: Client,
    event_payload: dict[str, object],
    member: Member,
    *,
    update: bool,
) -> None:
    """Одинаковые назначения отклоняются без частичного сохранения."""
    url = EVENTS_URL
    if update:
        response = editor_client.post(
            url,
            event_payload,
            content_type=JSON_MIME,
        )
        event_id = response.json()[ID_KEY]
        url = f'{url}{event_id}/'
    event_payload[NAME_KEY] = 'Новое название'
    event_payload[ORGANIZERS_KEY] = [
        {MEMBER_KEY: member.pk, ROLE_KEY: HOST_ROLE},
        {MEMBER_KEY: member.pk, ROLE_KEY: HOST_ROLE},
    ]
    response = editor_client.generic(
        'PUT' if update else 'POST',
        url,
        data=json.dumps(event_payload),
        content_type=JSON_MIME,
    )
    assert response.status_code == 409
    if update:
        card = editor_client.get(url).json()
        assert card[NAME_KEY] == 'День факультета'
        assert len(card[ORGANIZERS_KEY]) == 1
    else:
        assert not Event.objects.exists()


@pytest.mark.django_db
def test_event_deleted_member_rollback(
    editor_client: Client,
    event_payload: dict[str, object],
    member: Member,
) -> None:
    """Удалённый активист не может получить назначение при обновлении."""
    created = editor_client.post(
        EVENTS_URL,
        event_payload,
        content_type=JSON_MIME,
    ).json()
    member.delete()
    url = f'/api/events/{created[ID_KEY]}/'
    event_payload[NAME_KEY] = 'Не сохранять'  # noqa: RUF001
    response = editor_client.put(
        url,
        event_payload,
        content_type=JSON_MIME,
    )
    assert response.status_code == 400
    card = editor_client.get(url).json()
    assert (
        card[NAME_KEY],
        card[ORGANIZERS_KEY],
        EventOrganizer.objects.count(),
        editor_client.get(f'/api/members/{member.pk}/events/').status_code,
    ) == (
        'День факультета',
        [],
        1,
        404,
    )


@pytest.mark.django_db
def test_event_lists_search_and_memberships(
    editor_client: Client,
    scheduled_events: tuple[Event, Event],
) -> None:
    """Список сортируется, поддерживает пагинацию и нечёткий поиск."""
    first, second = scheduled_events
    assert [
        entry[ID_KEY] for entry in editor_client.get(EVENTS_URL).json()
    ] == [
        second.pk,
        first.pk,
    ]
    page = editor_client.get(
        '/api/events/?sort_by=starts_at&limit=1&offset=1',
    ).json()
    assert [entry[ID_KEY] for entry in page] == [second.pk]
    assert ORGANIZERS_KEY not in page[0]
    assert [
        entry[ID_KEY]
        for entry in editor_client.get(
            '/api/events/?search=Спортивный%20турни',  # noqa: RUF001
        ).json()
    ] == [second.pk]
    assert editor_client.get('/api/events/?search=несовпадение').json() == []


@pytest.mark.django_db
def test_memberships_hide_deleted_events(
    editor_client: Client,
    scheduled_events: tuple[Event, Event],
    member: Member,
) -> None:
    """Членства содержат роли и краткие события, учитывают мягкое удаление."""
    first, second = scheduled_events
    url = f'/api/members/{member.pk}/events/'
    memberships = editor_client.get(url).json()
    assert (
        [entry['event'][ID_KEY] for entry in memberships],
        {entry['role'] for entry in memberships[:2]},
        'organizers' in memberships[0]['event'],
    ) == ([second.pk, second.pk, first.pk], {HOST_ROLE, ORGANIZER_ROLE}, False)
    assert (
        editor_client.get(f'{url}?sort_by=starts_at&limit=1&offset=0').json()[
            0
        ]['event']['id']
        == first.pk
    )
    assert str(second) == 'Спортивный турнир'
    second.delete()
    assert (
        Event.objects.filter(pk=second.pk).exists(),
        Event.all_objects.filter(pk=second.pk).exists(),
        EventOrganizer.objects.filter(event_id=second.pk).count(),
        len(editor_client.get(url).json()),
    ) == (False, True, 2, 1)
    second.restore()
    assert len(editor_client.get(url).json()) == 3


@pytest.mark.django_db
@pytest.mark.parametrize(
    'query',
    [
        'sort_by=name',
        'limit=0',
        'limit=1001',
        'offset=-1',
    ],
)
def test_event_bad_query(viewer_client: Client, query: str) -> None:
    """Отклоняет недопустимую сортировку и пагинацию."""
    assert viewer_client.get(f'/api/events/?{query}').status_code == 400
