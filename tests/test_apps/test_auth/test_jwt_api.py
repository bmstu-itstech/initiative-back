from http import HTTPStatus
from typing import final
from unittest.mock import patch

import pytest
from django.contrib.auth.models import AnonymousUser, User
from django.urls import reverse
from dmr.test import DMRClient


@final
@pytest.mark.django_db
class TestJWTAPI:
    """Тесты для контроллеров аутентификации (Login и Refresh)."""

    def test_login_invalid_user_instance(self, dmr_client: DMRClient) -> None:
        """Имитируем ситуацию, когда authenticate вернул не модель User."""
        with patch(
            'server.apps.auth.controllers.jwt.authenticate',
            return_value=AnonymousUser(),
        ):
            response = dmr_client.post(
                reverse('api:auth:login'),
                data={'username': 'test', 'password': '123'},
            )
            assert response.status_code == HTTPStatus.UNAUTHORIZED
            assert (
                response.json()['detail'][0]['msg'] == 'Ошибка аутентификации.'
            )

    def test_refresh_success(
        self,
        dmr_client: DMRClient,
        viewer_user: User,
    ) -> None:
        """Успешное обновление токена."""
        login_response = dmr_client.post(
            reverse('api:auth:login'),
            data={'username': 'viewer_test', 'password': 'password123'},
        )
        refresh_token = login_response.json()['refresh_token']

        response = dmr_client.post(
            reverse('api:auth:refresh'),
            data={'refresh': refresh_token},
        )
        assert response.status_code == HTTPStatus.OK
        assert 'access_token' in response.json()
        assert 'refresh_token' in response.json()

    def test_refresh_with_access_token(
        self,
        dmr_client: DMRClient,
        viewer_user: User,
    ) -> None:
        """Попытка использовать access_token вместо refresh_token."""
        login_response = dmr_client.post(
            reverse('api:auth:login'),
            data={'username': 'viewer_test', 'password': 'password123'},
        )
        access_token = login_response.json()['access_token']

        response = dmr_client.post(
            reverse('api:auth:refresh'),
            data={'refresh': access_token},
        )
        assert response.status_code == HTTPStatus.UNAUTHORIZED
        assert response.json()['detail'][0]['msg'] == 'Это не refresh токен'

    def test_refresh_user_deleted(
        self,
        dmr_client: DMRClient,
        viewer_user: User,
    ) -> None:
        """Токен валидный, но пользователя удалили из БД."""
        login_response = dmr_client.post(
            reverse('api:auth:login'),
            data={'username': 'viewer_test', 'password': 'password123'},
        )
        refresh_token = login_response.json()['refresh_token']

        viewer_user.delete()

        response = dmr_client.post(
            reverse('api:auth:refresh'),
            data={'refresh': refresh_token},
        )
        assert response.status_code == HTTPStatus.UNAUTHORIZED
        assert response.json()['detail'][0]['msg'] == 'Пользователь не найден.'
