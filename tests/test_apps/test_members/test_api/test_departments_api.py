from http import HTTPStatus
from typing import final

import msgspec
import pytest
from django.urls import reverse
from dmr.test import DMRClient

from server.apps.members.logic.value_objects import DepartmentIn, DepartmentOut
from server.apps.members.models import Department, Direction


@final
@pytest.mark.django_db
class TestDepartmentsAPI:
    """Тесты API для сущности Отделы (Departments)."""

    def test_department_create(
        self,
        dmr_client: DMRClient,
        direction: Direction,
        department_in: DepartmentIn,
    ) -> None:
        """Успешное создание отдела."""
        department_in.direction_id = direction.id
        payload = msgspec.to_builtins(department_in)

        response = dmr_client.post(
            reverse('api:members:departments'),
            data=payload,
        )
        assert response.status_code == HTTPStatus.CREATED

        data = msgspec.convert(response.json(), type=DepartmentOut)
        assert data.name == department_in.name
        assert data.direction.id == direction.id

    def test_department_get_list(
        self,
        dmr_client: DMRClient,
        department: Department,
    ) -> None:
        """Получение списка отделов."""
        response = dmr_client.get(reverse('api:members:departments'))
        assert response.status_code == HTTPStatus.OK
        assert len(response.json()) >= 1

    def test_department_update(
        self,
        dmr_client: DMRClient,
        department: Department,
        direction: Direction,
        department_in: DepartmentIn,
    ) -> None:
        """Успешное обновление отдела."""
        department_in.direction_id = direction.id
        department_in.name = 'Новое имя отдела'
        response = dmr_client.put(
            reverse(
                'api:members:department_detail',
                kwargs={'department_id': department.id},
            ),
            data=msgspec.to_builtins(department_in),
        )

        assert response.status_code == HTTPStatus.OK
        department.refresh_from_db()
        assert department.name == 'Новое имя отдела'

    def test_department_delete(
        self,
        dmr_client: DMRClient,
        department: Department,
    ) -> None:
        """Мягкое удаление отдела."""
        response = dmr_client.delete(
            reverse(
                'api:members:department_detail',
                kwargs={'department_id': department.id},
            ),
        )
        assert response.status_code == HTTPStatus.OK
        department.refresh_from_db()
        assert department.is_deleted is True

    def test_department_get_not_found(self, dmr_client: DMRClient) -> None:
        """Ошибка получения несуществующего отдела."""
        response = dmr_client.get(
            reverse(
                'api:members:department_detail',
                kwargs={'department_id': 999999},
            ),
        )
        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_department_create_duplicate(
        self,
        dmr_client: DMRClient,
        department: Department,
        direction: Direction,
        department_in: DepartmentIn,
    ) -> None:
        """Ошибка создания дубликата отдела (Conflict)."""
        department_in.name = department.name
        department_in.direction_id = direction.id
        payload = msgspec.to_builtins(department_in)

        response = dmr_client.post(
            reverse('api:members:departments'),
            data=payload,
        )
        assert response.status_code == HTTPStatus.CONFLICT

    def test_department_update_not_found(
        self,
        dmr_client: DMRClient,
        department_in: DepartmentIn,
    ) -> None:
        """Ошибка обновления несуществующего отдела."""
        response = dmr_client.put(
            reverse(
                'api:members:department_detail',
                kwargs={'department_id': 999999},
            ),
            data=msgspec.to_builtins(department_in),
        )
        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_department_get_detail(
        self,
        dmr_client: DMRClient,
        department: Department,
    ) -> None:
        """Успешное получение конкретного отдела по ID."""
        response = dmr_client.get(
            reverse(
                'api:members:department_detail',
                kwargs={'department_id': department.id},
            ),
        )
        assert response.status_code == HTTPStatus.OK
        assert response.json()['id'] == department.id

    def test_department_update_duplicate(
        self,
        dmr_client: DMRClient,
        department: Department,
        direction: Direction,
        department_in: DepartmentIn,
    ) -> None:
        """Ошибка обновления отдела: такое имя уже занято (Conflict)."""
        other_department = Department.objects.create(
            name='Другой отдел',
            direction=direction,
        )

        department_in.name = other_department.name
        department_in.direction_id = direction.id

        response = dmr_client.put(
            reverse(
                'api:members:department_detail',
                kwargs={'department_id': department.id},
            ),
            data=msgspec.to_builtins(department_in),
        )
        assert response.status_code == HTTPStatus.CONFLICT
