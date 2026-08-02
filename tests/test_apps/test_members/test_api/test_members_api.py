import json
from collections.abc import Mapping
from http import HTTPStatus
from typing import Any, final

import msgspec
import pytest
from django.urls import reverse
from dmr.parsers import JsonParser
from dmr.test import DMRClient

from server.apps.members.controllers.members import FallbackHtmlRenderer
from server.apps.members.logic.value_objects import MemberIn, MemberOut
from server.apps.members.models import Department, Direction, Leader, Member


@final
@pytest.mark.django_db
class TestMembersAPI:
    """Тесты API для Активистов."""

    def test_member_create(
        self,
        dmr_client: DMRClient,
        department: Department,
        member_in: MemberIn,
        auth_headers_editor: Mapping[str, Any],
    ) -> None:
        """Успешное создание активиста."""
        member_in.department_ids = [department.id]
        response = dmr_client.post(
            reverse('api:members:members'),
            data=msgspec.to_builtins(member_in),
            **auth_headers_editor,
        )

        assert response.status_code == HTTPStatus.CREATED
        data = msgspec.convert(response.json(), type=MemberOut)
        assert data.telegram == member_in.telegram
        assert len(data.departments) == 1

    def test_member_get_list(
        self,
        dmr_client: DMRClient,
        member: Member,
        auth_headers_editor: Mapping[str, Any],
    ) -> None:
        """Успешное получение списка активистов."""
        response = dmr_client.get(
            reverse('api:members:members'),
            **auth_headers_editor,
        )
        assert response.status_code == HTTPStatus.OK
        assert len(response.json()) >= 1

    def test_member_delete(
        self,
        dmr_client: DMRClient,
        member: Member,
        auth_headers_editor: Mapping[str, Any],
    ) -> None:
        """Мягкое удаление активиста."""
        response = dmr_client.delete(
            reverse(
                'api:members:member_detail',
                kwargs={'member_id': member.id},
            ),
            **auth_headers_editor,
        )
        assert response.status_code == HTTPStatus.OK
        member.refresh_from_db()
        assert member.deleted_at is not None

    def test_member_get_not_found(
        self,
        dmr_client: DMRClient,
        auth_headers_editor: Mapping[str, Any],
    ) -> None:
        """Ошибка получения несуществующего активиста."""
        response = dmr_client.get(
            reverse(
                'api:members:member_detail',
                kwargs={'member_id': 999999},
            ),
            **auth_headers_editor,
        )
        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_member_create_duplicate(
        self,
        dmr_client: DMRClient,
        member: Member,
        member_in: MemberIn,
        auth_headers_editor: Mapping[str, Any],
    ) -> None:
        """Ошибка создания активиста с существующим Telegram (Conflict)."""  # noqa: RUF002
        member_in.telegram = member.telegram
        payload = msgspec.to_builtins(member_in)

        response = dmr_client.post(
            reverse('api:members:members'),
            data=payload,
            **auth_headers_editor,
        )
        assert response.status_code == HTTPStatus.CONFLICT

    def test_member_delete_not_found(
        self,
        dmr_client: DMRClient,
        auth_headers_editor: Mapping[str, Any],
    ) -> None:
        """Удаления несуществующего активиста."""
        response = dmr_client.delete(
            reverse(
                'api:members:member_detail',
                kwargs={'member_id': 999999},
            ),
            **auth_headers_editor,
        )
        assert response.status_code == HTTPStatus.OK

    def test_member_get_detail(
        self,
        dmr_client: DMRClient,
        member: Member,
        auth_headers_editor: Mapping[str, Any],
    ) -> None:
        """Успешное получение конкретного активиста."""
        response = dmr_client.get(
            reverse(
                'api:members:member_detail',
                kwargs={'member_id': member.id},
            ),
            **auth_headers_editor,
        )
        assert response.status_code == HTTPStatus.OK
        assert response.json()['id'] == member.id

    def test_member_update_success(
        self,
        dmr_client: DMRClient,
        member: Member,
        member_in: MemberIn,
        department: Department,
        auth_headers_editor: Mapping[str, Any],
    ) -> None:
        """Успешное обновление активиста (PUT)."""
        member_in.first_name = 'ОбновленноеИмя'
        member_in.telegram = member.telegram

        member_in.department_ids = [department.id]

        payload = msgspec.to_builtins(member_in)

        response = dmr_client.put(
            reverse(
                'api:members:member_detail',
                kwargs={'member_id': member.id},
            ),
            data=payload,
            **auth_headers_editor,
        )
        assert response.status_code == HTTPStatus.OK
        assert response.json()['first_name'] == 'ОбновленноеИмя'

    def test_member_update_duplicate(
        self,
        dmr_client: DMRClient,
        member: Member,
        member_in: MemberIn,
        auth_headers_editor: Mapping[str, Any],
    ) -> None:
        """Ошибка обновления активиста: Telegram занят (Conflict)."""
        second_member = Member.objects.create(
            first_name='2',
            last_name='2',
            telegram='telegram2',
        )
        member_in.telegram = second_member.telegram

        payload = msgspec.to_builtins(member_in)
        response = dmr_client.put(
            reverse(
                'api:members:member_detail',
                kwargs={'member_id': member.id},
            ),
            data=payload,
            **auth_headers_editor,
        )
        assert response.status_code == HTTPStatus.CONFLICT

    def test_get_members_by_department(
        self,
        dmr_client: DMRClient,
        member: Member,
        department: Department,
        auth_headers_editor: Mapping[str, Any],
    ) -> None:
        """Успешное получение активистов отдела."""
        member.departments.add(department)
        response = dmr_client.get(
            reverse(
                'api:members:department_members',
                kwargs={'department_id': department.id},
            ),
            **auth_headers_editor,
        )
        assert response.status_code == HTTPStatus.OK
        assert len(response.json()) >= 1

    def test_get_members_by_direction(
        self,
        dmr_client: DMRClient,
        member: Member,
        department: Department,
        auth_headers_editor: Mapping[str, Any],
    ) -> None:
        """Успешное получение активистов направления."""
        member.departments.add(department)
        response = dmr_client.get(
            reverse(
                'api:members:direction_members',
                kwargs={'direction_id': department.direction_id},
            ),
            **auth_headers_editor,
        )
        assert response.status_code == HTTPStatus.OK
        assert len(response.json()) >= 1

    def test_member_export_success(
        self,
        dmr_client: DMRClient,
        member: Member,
        auth_headers_editor: Mapping[str, Any],
    ) -> None:
        """Успешный экспорт активистов в CSV."""
        response = dmr_client.get(
            reverse('api:members:member_export'),
            **auth_headers_editor,
        )
        assert response.status_code == HTTPStatus.OK
        assert 'text/csv' in response.headers.get('Content-Type', '')
        assert b'id;last_name;first_name' in response.content
        assert str(member.id).encode() in response.content

    def test_member_export_unauthorized_html_fallback(
        self,
        dmr_client: DMRClient,
    ) -> None:
        """Тест перехвата браузерного запроса без токена (Accept: text/html)."""
        response = dmr_client.get(
            reverse('api:members:member_export'),
            HTTP_ACCEPT='text/html',
        )

        assert response.status_code == HTTPStatus.UNAUTHORIZED

        data = json.loads(response.content)
        assert 'detail' in data

    def test_fallback_html_renderer(self) -> None:
        """Прямой юнит-тест рендерера для 100% покрытия кода."""
        renderer = FallbackHtmlRenderer()

        data = {'error': 'test_error'}
        rendered_bytes = renderer.render(data, serializer_hook=str)
        assert rendered_bytes == json.dumps(data).encode('utf-8')

        parser = renderer.validation_parser
        assert isinstance(parser, JsonParser)

    def test_members_structure_get(
        self,
        dmr_client: DMRClient,
        direction: Direction,
        department: Department,
        leader: Leader,
        auth_headers_viewer: Mapping[str, Any],
    ) -> None:
        """Успешное получение древовидной структуры (N+1 free)."""
        response = dmr_client.get(
            reverse('api:members:members_structure'),
            **auth_headers_viewer,
        )

        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

        dir_data = next(d for d in data if d['id'] == direction.id)
        assert 'departments' in dir_data
        assert 'leaders' in dir_data

        dept_data = next(
            d for d in dir_data['departments'] if d['id'] == department.id
        )
        assert 'members' in dept_data
        assert 'leaders' in dept_data
