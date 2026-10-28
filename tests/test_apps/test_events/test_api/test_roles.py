import pytest
from django.contrib.auth.models import Group, User
from django.test import Client

from server.apps.events.models import EventOrganizer
from server.apps.members.models import Member

JSON_MIME = 'application/json'


@pytest.mark.django_db
def test_admin_can_write_events(
    client: Client,
    event_payload: dict[str, object],
) -> None:
    """Группа Admin разрешает создание, обновление и мягкое удаление."""
    account = User.objects.create_user(
        username='event_admin',
        password='test123',  # noqa: S106
    )
    account.groups.add(Group.objects.get_or_create(name='Admin')[0])
    token = client.post(
        '/api/auth/login/',
        {'username': 'event_admin', 'password': 'test123'},
        content_type=JSON_MIME,
    ).json()['access_token']
    client.defaults['HTTP_AUTHORIZATION'] = f'Bearer {token}'
    response = client.post(
        '/api/events/',
        event_payload,
        content_type=JSON_MIME,
    )
    assert response.status_code == 201
    event_id = response.json()['id']
    event_url = f'/api/events/{event_id}/'
    assert (
        client.put(
            event_url,
            event_payload,
            content_type=JSON_MIME,
        ).status_code,
        client.delete(event_url).status_code,
        client.get(event_url).status_code,
    ) == (
        200,
        200,
        404,
    )


@pytest.mark.django_db
def test_same_role_for_different_members(
    editor_client: Client,
    event_payload: dict[str, object],
    member: Member,
) -> None:
    """Одна строковая роль допускает несколько разных активистов."""
    another = Member.objects.create(
        first_name='Пётр',
        last_name='Петров',
        telegram='another',
    )
    event_payload['organizers'] = [
        {'member_id': activist_id, 'role': 'Ведущий'}
        for activist_id in (member.pk, another.pk)
    ]
    response = editor_client.post(
        '/api/events/',
        event_payload,
        content_type=JSON_MIME,
    )
    assert (
        response.status_code,
        len(response.json()['organizers']),
        set(EventOrganizer.objects.values_list('member_id', flat=True)),
    ) == (
        201,
        2,
        {member.pk, another.pk},
    )
