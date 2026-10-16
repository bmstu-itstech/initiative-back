from collections.abc import Mapping
from http import HTTPStatus
from typing import Any, final

import msgspec
import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from dmr.test import DMRClient

from server.apps.members.logic.value_objects import LeaderIn, LeaderOut
from server.apps.members.models import Department, Direction, Leader, Member


@final
@pytest.mark.django_db
class TestLeadersAPI:
    """Тесты API для Руководителей."""

    @pytest.mark.parametrize('authenticated', [False, True])
    def test_leader_list_access_denied(
        self,
        dmr_client: DMRClient,
        viewer_user: User,
        auth_headers_viewer: Mapping[str, Any],
        *,
        authenticated: bool,
    ) -> None:
        """Запрещает чтение списка без JWT или необходимой роли."""
        viewer_user.groups.clear()
        headers = auth_headers_viewer if authenticated else {}
        response = dmr_client.get(
            reverse('api:members:leaders'),
            **headers,
        )
        expected = (
            HTTPStatus.FORBIDDEN if authenticated else HTTPStatus.UNAUTHORIZED
        )
        assert response.status_code == expected

    def test_leader_list_nested_relations(
        self,
        dmr_client: DMRClient,
        leader: Leader,
        member: Member,
        department: Department,
        auth_headers_viewer: Mapping[str, Any],
    ) -> None:
        """Сохраняет вложенные данные и мягкое удаление при чтении Viewer."""
        direction = Direction.objects.create(name='Другое направление')
        other_department = Department.objects.create(
            name='Другой отдел',
            direction=direction,
        )
        deleted_department = Department.objects.create(
            name='Удалённый отдел',
            direction=direction,
        )
        member.departments.add(
            department,
            other_department,
            deleted_department,
        )
        deleted_department.delete()
        direction.delete()
        second = Leader.objects.create(
            member=member,
            position='Руководитель направления',
            direction=direction,
        )
        deleted_leader = Leader.objects.create(
            member=member,
            position='Удалённое назначение',
        )
        deleted_leader.delete()
        member.delete()

        response = dmr_client.get(
            reverse('api:members:leaders'),
            **auth_headers_viewer,
        )

        assert response.status_code == HTTPStatus.OK
        result = msgspec.convert(response.json(), type=list[LeaderOut])
        assert {item.id for item in result} == {leader.pk, second.pk}
        for item in result:
            assert item.member.id == member.pk
            assert item.member.first_name == member.first_name
            assert item.member.telegram == member.telegram
            assert {dep.id for dep in item.member.departments} == {
                department.pk,
                other_department.pk,
            }
            assert {dep.direction.id for dep in item.member.departments} == {
                department.direction_id,
                direction.pk,
            }
        by_id = {item.id: item for item in result}
        assert by_id[leader.pk].department is not None
        assert by_id[leader.pk].direction is None
        assert by_id[second.pk].department is None
        assert by_id[second.pk].direction is not None

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

        payload = {
            'member_id': new_member.id,
            'position': leader.position,
            'department_id': leader.department_id
            if leader.department
            else None,
            'direction_id': leader.direction_id if leader.direction else None,
        }

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
        """Удаления несуществующего руководителя."""
        response = dmr_client.delete(
            reverse(
                'api:members:leader_detail',
                kwargs={'leader_id': 999999},
            ),
            **auth_headers_editor,
        )
        assert response.status_code == HTTPStatus.OK

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
