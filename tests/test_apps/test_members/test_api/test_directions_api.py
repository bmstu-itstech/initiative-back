from collections.abc import Mapping
from http import HTTPStatus
from typing import Any, final

import msgspec
import pytest
from django.urls import reverse
from dmr.test import DMRClient

from server.apps.members.logic.value_objects import DirectionIn, DirectionOut
from server.apps.members.models import Direction


@final
@pytest.mark.django_db
class TestDirectionsAPI:
    """Тесты API для сущности Направления (Directions)."""

    def test_direction_create(
        self,
        dmr_client: DMRClient,
        direction_in: DirectionIn,
        auth_headers_editor: Mapping[str, Any],
    ) -> None:
        """Успешное создание направления."""
        payload = msgspec.to_builtins(direction_in)

        response = dmr_client.post(
            reverse('api:members:directions'),
            data=payload,
            **auth_headers_editor,
        )

        assert response.status_code == HTTPStatus.CREATED
        direction_out = msgspec.convert(response.json(), type=DirectionOut)
        assert direction_out.name == payload['name']
        assert Direction.objects.filter(id=direction_out.id).exists()

    def test_direction_create_duplicate(
        self,
        dmr_client: DMRClient,
        direction: Direction,
        direction_in: DirectionIn,
        auth_headers_editor: Mapping[str, Any],
    ) -> None:
        """Ошибка создания направления с существующим именем (Conflict)."""  # noqa: RUF002
        direction_in.name = direction.name
        payload = msgspec.to_builtins(direction_in)

        response = dmr_client.post(
            reverse('api:members:directions'),
            data=payload,
            **auth_headers_editor,
        )

        assert response.status_code == HTTPStatus.CONFLICT
        assert 'уже существует' in response.json()['detail'][0]['msg']

    def test_direction_delete_not_found(
        self,
        dmr_client: DMRClient,
        auth_headers_editor: Mapping[str, Any],
    ) -> None:
        """Удаления несуществующего направления."""
        response = dmr_client.delete(
            reverse(
                'api:members:direction_detail',
                kwargs={'direction_id': 999999},
            ),
            **auth_headers_editor,
        )
        assert response.status_code == HTTPStatus.OK

    def test_direction_get_list(
        self,
        dmr_client: DMRClient,
        direction: Direction,
        auth_headers_editor: Mapping[str, Any],
    ) -> None:
        """Получение списка направлений."""
        response = dmr_client.get(
            reverse('api:members:directions'),
            **auth_headers_editor,
        )

        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(item['id'] == direction.id for item in data)

    def test_direction_get_detail(
        self,
        dmr_client: DMRClient,
        direction: Direction,
        auth_headers_editor: Mapping[str, Any],
    ) -> None:
        """Получение конкретного направления по ID."""
        response = dmr_client.get(
            reverse(
                'api:members:direction_detail',
                kwargs={'direction_id': direction.id},
            ),
            **auth_headers_editor,
        )

        assert response.status_code == HTTPStatus.OK
        direction_out = msgspec.convert(response.json(), type=DirectionOut)
        assert direction_out.id == direction.id

    def test_direction_get_not_found(
        self,
        dmr_client: DMRClient,
        auth_headers_editor: Mapping[str, Any],
    ) -> None:
        """Ошибка получения несуществующего направления."""
        response = dmr_client.get(
            reverse(
                'api:members:direction_detail',
                kwargs={'direction_id': 999999},
            ),
            **auth_headers_editor,
        )

        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_direction_update(
        self,
        dmr_client: DMRClient,
        direction: Direction,
        direction_in: DirectionIn,
        auth_headers_editor: Mapping[str, Any],
    ) -> None:
        """Успешное обновление направления."""
        direction_in.name = 'Обновленное Имя'
        payload = msgspec.to_builtins(direction_in)

        response = dmr_client.put(
            reverse(
                'api:members:direction_detail',
                kwargs={'direction_id': direction.id},
            ),
            data=payload,
            **auth_headers_editor,
        )

        assert response.status_code == HTTPStatus.OK
        direction.refresh_from_db()
        assert direction.name == 'Обновленное Имя'

    def test_direction_delete(
        self,
        dmr_client: DMRClient,
        direction: Direction,
        auth_headers_editor: Mapping[str, Any],
    ) -> None:
        """Мягкое удаление направления."""
        response = dmr_client.delete(
            reverse(
                'api:members:direction_detail',
                kwargs={'direction_id': direction.id},
            ),
            **auth_headers_editor,
        )

        assert response.status_code == HTTPStatus.OK
        direction.refresh_from_db()
        assert direction.deleted_at is not None

    def test_direction_update_not_found(
        self,
        dmr_client: DMRClient,
        direction_in: DirectionIn,
        auth_headers_editor: Mapping[str, Any],
    ) -> None:
        """Ошибка обновления несуществующего направления."""
        response = dmr_client.put(
            reverse(
                'api:members:direction_detail',
                kwargs={'direction_id': 999999},
            ),
            data=msgspec.to_builtins(direction_in),
            **auth_headers_editor,
        )
        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_direction_update_duplicate(
        self,
        dmr_client: DMRClient,
        direction: Direction,
        direction_in: DirectionIn,
        auth_headers_editor: Mapping[str, Any],
    ) -> None:
        """Ошибка обновления направления: такое имя уже занято (Conflict)."""
        other_direction = Direction.objects.create(name='Другое направление')

        direction_in.name = other_direction.name
        payload = msgspec.to_builtins(direction_in)

        response = dmr_client.put(
            reverse(
                'api:members:direction_detail',
                kwargs={'direction_id': direction.id},
            ),
            data=payload,
            **auth_headers_editor,
        )

        assert response.status_code == HTTPStatus.CONFLICT
