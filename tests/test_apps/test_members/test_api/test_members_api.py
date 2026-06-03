from http import HTTPStatus
from typing import final

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
    ) -> None:
        """Успешное создание активиста."""
        member_in.department_ids = [department.id]
        response = dmr_client.post(
            reverse('api:members:members'),
            data=msgspec.to_builtins(member_in),
        )

        assert response.status_code == HTTPStatus.CREATED
        data = msgspec.convert(response.json(), type=MemberOut)
        assert data.telegram == member_in.telegram
        assert len(data.departments) == 1

    def test_member_get_list(
        self,
        dmr_client: DMRClient,
        member: Member,
    ) -> None:
        """Успешное получение списка активистов."""
        response = dmr_client.get(
            reverse('api:members:members'),
        )
        assert response.status_code == HTTPStatus.OK
        assert len(response.json()) >= 1

    def test_member_delete(self, dmr_client: DMRClient, member: Member) -> None:
        """Мягкое удаление активиста."""
        response = dmr_client.delete(
            reverse(
                'api:members:member_detail',
                kwargs={'member_id': member.id},
            ),
        )
        assert response.status_code == HTTPStatus.OK
        member.refresh_from_db()
        assert member.is_deleted is True

    def test_member_get_not_found(self, dmr_client: DMRClient) -> None:
        """Ошибка получения несуществующего активиста."""
        response = dmr_client.get(
            reverse(
                'api:members:member_detail',
                kwargs={'member_id': 999999},
            ),
        )
        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_member_create_duplicate(
        self,
        dmr_client: DMRClient,
        member: Member,
        member_in: MemberIn,
    ) -> None:
        """Ошибка создания активиста с существующим Telegram (Conflict)."""  # noqa: RUF002
        member_in.telegram = member.telegram
        payload = msgspec.to_builtins(member_in)

        response = dmr_client.post(
            reverse('api:members:members'),
            data=payload,
        )
        assert response.status_code == HTTPStatus.CONFLICT

    def test_member_get_detail(
        self,
        dmr_client: DMRClient,
        member: Member,
    ) -> None:
        """Успешное получение конкретного активиста."""
        response = dmr_client.get(
            reverse(
                'api:members:member_detail',
                kwargs={'member_id': member.id},
            ),
        )
        assert response.status_code == HTTPStatus.OK
        assert response.json()['id'] == member.id

    def test_member_update_success(
        self,
        dmr_client: DMRClient,
        member: Member,
        member_in: MemberIn,
        department: Department,
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
        )
        assert response.status_code == HTTPStatus.OK
        assert response.json()['first_name'] == 'ОбновленноеИмя'

    def test_member_update_duplicate(
        self,
        dmr_client: DMRClient,
        member: Member,
        member_in: MemberIn,
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
        )
        assert response.status_code == HTTPStatus.CONFLICT

    def test_get_members_by_department(
        self,
        dmr_client: DMRClient,
        member: Member,
        department: Department,
    ) -> None:
        """Успешное получение активистов отдела."""
        member.departments.add(department)
        response = dmr_client.get(
            reverse(
                'api:members:department_members',
                kwargs={'department_id': department.id},
            ),
        )
        assert response.status_code == HTTPStatus.OK
        assert len(response.json()) >= 1

    def test_get_members_by_direction(
        self,
        dmr_client: DMRClient,
        member: Member,
        department: Department,
    ) -> None:
        """Успешное получение активистов направления."""
        member.departments.add(department)
        response = dmr_client.get(
            reverse(
                'api:members:direction_members',
                kwargs={'direction_id': department.direction_id},
            ),
        )
        assert response.status_code == HTTPStatus.OK
        assert len(response.json()) >= 1
