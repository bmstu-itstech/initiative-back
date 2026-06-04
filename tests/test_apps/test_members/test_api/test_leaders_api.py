from collections.abc import Mapping
from http import HTTPStatus
from typing import Any, final

import msgspec
import pytest
from django.urls import reverse
from dmr.test import DMRClient

from server.apps.members.logic.value_objects import LeaderIn, LeaderOut
from server.apps.members.models import Department, Leader, Member


@final
@pytest.mark.django_db
class TestLeadersAPI:
    """Тесты API для Руководителей."""

    def test_leader_create(
        self,
        dmr_client: DMRClient,
        member: Member,
        department: Department,
        leader_in: LeaderIn,
        auth_headers_editor: Mapping[str, Any],
    ) -> None:
        """Успешное создание руководителя с отделом."""  # noqa: RUF002
        leader_in.member_id = member.id
        leader_in.department_id = department.id
        leader_in.direction_id = None

        response = dmr_client.post(
            reverse('api:members:leaders'),
            data=msgspec.to_builtins(leader_in),
            **auth_headers_editor,
        )
        assert response.status_code == HTTPStatus.CREATED

        data = msgspec.convert(response.json(), type=LeaderOut)
        assert data.member.id == member.id
        assert data.department is not None
        assert data.department.id == department.id

    def test_leader_create_no_units(
        self,
        dmr_client: DMRClient,
        member: Member,
        leader_in: LeaderIn,
        auth_headers_editor: Mapping[str, Any],
    ) -> None:
        """Успешное создание руководителя без привязки к подразделениям."""
        leader_in.member_id = member.id
        leader_in.department_id = None
        leader_in.direction_id = None

        response = dmr_client.post(
            reverse('api:members:leaders'),
            data=msgspec.to_builtins(leader_in),
            **auth_headers_editor,
        )
        assert response.status_code == HTTPStatus.CREATED

        data = msgspec.convert(response.json(), type=LeaderOut)
        assert data.member.id == member.id
        assert data.department is None
        assert data.direction is None

    def test_leader_delete(
        self,
        dmr_client: DMRClient,
        leader: Leader,
        auth_headers_editor: Mapping[str, Any],
    ) -> None:
        """Мягкое удаление руководителя."""
        response = dmr_client.delete(
            reverse(
                'api:members:leader_detail',
                kwargs={'leader_id': leader.id},
            ),
            **auth_headers_editor,
        )
        assert response.status_code == HTTPStatus.OK
        leader.refresh_from_db()
        assert leader.deleted_at is not None

    def test_leader_get_not_found(
        self,
        dmr_client: DMRClient,
        auth_headers_editor: Mapping[str, Any],
    ) -> None:
        """Ошибка получения несуществующего руководителя."""
        response = dmr_client.get(
            reverse(
                'api:members:leader_detail',
                kwargs={'leader_id': 999999},
            ),
            **auth_headers_editor,
        )
        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_leader_create_duplicate(
        self,
        dmr_client: DMRClient,
        leader: Leader,
        leader_in: LeaderIn,
        auth_headers_editor: Mapping[str, Any],
    ) -> None:
        """Ошибка создания дубликата руководителя."""
        new_member = Member.objects.create(
            first_name='Новый',
            last_name='Активист',
            telegram='new_tg_user',
        )

        leader_in.member_id = new_member.id
        leader_in.position = leader.position
        leader_in.department_id = (
            leader.department.id if leader.department else None
        )
        leader_in.direction_id = (
            leader.direction.id if leader.direction else None
        )

        payload = msgspec.to_builtins(leader_in)
        response = dmr_client.post(
            reverse('api:members:leaders'),
            data=payload,
            **auth_headers_editor,
        )

        assert response.status_code == HTTPStatus.CONFLICT
        assert 'занята' in response.content.decode('utf-8')

    def test_leader_delete_not_found(
        self,
        dmr_client: DMRClient,
        auth_headers_editor: Mapping[str, Any],
    ) -> None:
        """Ошибка удаления несуществующего руководителя."""
        response = dmr_client.delete(
            reverse(
                'api:members:leader_detail',
                kwargs={'leader_id': 999999},
            ),
            **auth_headers_editor,
        )
        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_leader_get_list(
        self,
        dmr_client: DMRClient,
        leader: Leader,
        auth_headers_editor: Mapping[str, Any],
    ) -> None:
        """Успешное получение списка руководителей."""
        response = dmr_client.get(
            reverse(
                'api:members:leaders',
            ),
            **auth_headers_editor,
        )
        assert response.status_code == HTTPStatus.OK
        assert len(response.json()) >= 1

    def test_leader_get_detail(
        self,
        dmr_client: DMRClient,
        leader: Leader,
        auth_headers_editor: Mapping[str, Any],
    ) -> None:
        """Успешное получение руководителя по ID."""
        response = dmr_client.get(
            reverse(
                'api:members:leader_detail',
                kwargs={'leader_id': leader.id},
            ),
            **auth_headers_editor,
        )
        assert response.status_code == HTTPStatus.OK
        assert response.json()['id'] == leader.id

    def test_leader_update_success(
        self,
        dmr_client: DMRClient,
        leader: Leader,
        leader_in: LeaderIn,
        auth_headers_editor: Mapping[str, Any],
    ) -> None:
        """Успешное обновление руководителя (PUT)."""
        leader_in.member_id = leader.member_id
        leader_in.position = 'Новая Должность'
        leader_in.department_id = leader.department_id
        leader_in.direction_id = leader.direction_id

        payload = msgspec.to_builtins(leader_in)
        response = dmr_client.put(
            reverse(
                'api:members:leader_detail',
                kwargs={'leader_id': leader.id},
            ),
            data=payload,
            **auth_headers_editor,
        )

        assert response.status_code == HTTPStatus.OK
        assert response.json()['position'] == 'Новая Должность'

    def test_leader_update_duplicate(
        self,
        dmr_client: DMRClient,
        leader: Leader,
        auth_headers_editor: Mapping[str, Any],
    ) -> None:
        """Ошибка обновления руководителя: должность занята (Conflict)."""
        second_member = Member.objects.create(
            first_name='Второй',
            last_name='Активист',
            telegram='tg_second',
        )
        leader_2 = Leader.objects.create(
            member_id=second_member.id,
            position='Какая-то другая должность',
            department_id=leader.department_id,
        )

        payload = {
            'member_id': leader_2.member_id,
            'position': leader.position,
            'department_id': leader.department_id,
            'direction_id': None,
        }

        response = dmr_client.put(
            reverse(
                'api:members:leader_detail',
                kwargs={'leader_id': leader_2.id},
            ),
            data=payload,
            **auth_headers_editor,
        )

        assert response.status_code == HTTPStatus.CONFLICT
        assert 'занята' in response.content.decode('utf-8')

    def test_leader_create_not_found(
        self,
        dmr_client: DMRClient,
        leader_in: LeaderIn,
        auth_headers_editor: Mapping[str, Any],
    ) -> None:
        """Ошибка создания руководителя с несуществующим активистом."""  # noqa: RUF002
        leader_in.member_id = 999999
        leader_in.department_id = None
        leader_in.direction_id = None

        payload = msgspec.to_builtins(leader_in)
        response = dmr_client.post(
            reverse('api:members:leaders'),
            data=payload,
            **auth_headers_editor,
        )

        assert response.status_code == HTTPStatus.NOT_FOUND
