from collections.abc import Mapping
from http import HTTPStatus
from typing import Any, final

import pytest
from django.urls import reverse
from dmr.test import DMRClient

from server.apps.members.models import Direction


@final
@pytest.mark.django_db
class TestAPISecurity:
    """Тесты ролевой модели (RBAC) и прав доступа."""

    def test_anonymous_access_denied(self, dmr_client: DMRClient) -> None:
        """Анонимный пользователь получает 401 Unauthorized на всё."""
        response_get = dmr_client.get(reverse('api:members:directions'))
        assert response_get.status_code == HTTPStatus.UNAUTHORIZED

        response_post = dmr_client.post(
            reverse('api:members:directions'),
            data={'name': 'Hack Direction'},
        )
        assert response_post.status_code == HTTPStatus.UNAUTHORIZED

    def test_viewer_access(
        self,
        dmr_client: DMRClient,
        auth_headers_viewer: Mapping[str, Any],
        direction: Direction,
    ) -> None:
        """Viewer может читать (GET), но не может изменять (POST/PUT/DELETE)."""
        response_get = dmr_client.get(
            reverse('api:members:directions'),
            **auth_headers_viewer,
        )
        assert response_get.status_code == HTTPStatus.OK

        response_post = dmr_client.post(
            reverse('api:members:directions'),
            data={'name': 'New Direction'},
            **auth_headers_viewer,
        )
        assert response_post.status_code == HTTPStatus.FORBIDDEN

        response_put = dmr_client.put(
            reverse(
                'api:members:direction_detail',
                kwargs={'direction_id': direction.id},
            ),
            data={'name': 'Changed Direction'},
            **auth_headers_viewer,
        )
        assert response_put.status_code == HTTPStatus.FORBIDDEN

        response_delete = dmr_client.delete(
            reverse(
                'api:members:direction_detail',
                kwargs={'direction_id': direction.id},
            ),
            **auth_headers_viewer,
        )
        assert response_delete.status_code == HTTPStatus.FORBIDDEN

    def test_superuser_access(
        self,
        dmr_client: DMRClient,
        auth_headers_superuser: Mapping[str, Any],
        direction: Direction,
    ) -> None:
        """Суперпользователь имеет доступ к любым действиям."""
        response_post = dmr_client.post(
            reverse('api:members:directions'),
            data={'name': 'Super Direction'},
            **auth_headers_superuser,
        )

        assert response_post.status_code in {
            HTTPStatus.CREATED,
            HTTPStatus.OK,
        }
