from collections.abc import Mapping
from http import HTTPStatus
from typing import Any, final

import msgspec
import pytest
from django.urls import reverse
from dmr.test import DMRClient

from server.apps.members.logic.value_objects import MemberIn, MemberOut
from server.apps.members.models import Department, Member


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
