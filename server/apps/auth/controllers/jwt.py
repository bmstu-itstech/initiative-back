import datetime as dt
import uuid
from http import HTTPStatus
from typing import Any, ClassVar, final

import jwt
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from dmr import Body, Controller, modify
from dmr.errors import ErrorModel
from dmr.exceptions import NotAuthenticatedError
from dmr.metadata import ResponseSpec
from dmr.plugins.msgspec import MsgspecSerializer
from dmr.security.jwt.token import JWToken

from server.apps.auth.logic.value_objects import LoginIn, RefreshIn, TokensOut


class _TokenMixin:
    """Общая логика для генерации токенов."""

    jwt_algorithm: ClassVar[str] = 'HS256'
    jwt_expiration: ClassVar[dt.timedelta] = dt.timedelta(days=1)
    jwt_refresh_expiration: ClassVar[dt.timedelta] = dt.timedelta(days=10)

    def generate_token_pair(self, user: User) -> TokensOut:
        """Генерирует access и refresh токены для пользователя."""
        now = dt.datetime.now(dt.UTC)

        access = JWToken(
            sub=str(user.pk),
            exp=now + self.jwt_expiration,
            jti=uuid.uuid4().hex,
            extras={'type': 'access'},
        ).encode(
            secret=settings.SECRET_KEY,
            algorithm=self.jwt_algorithm,
        )

        refresh = JWToken(
            sub=str(user.pk),
            exp=now + self.jwt_refresh_expiration,
            jti=uuid.uuid4().hex,
            extras={'type': 'refresh'},
        ).encode(
            secret=settings.SECRET_KEY,
            algorithm=self.jwt_algorithm,
        )

        return TokensOut(access_token=access, refresh_token=refresh)


@final
class LoginController(_TokenMixin, Controller[MsgspecSerializer]):
    """Контроллер для получения пары JWT токенов (Login)."""

    auth = None
    tags: ClassVar[tuple[str, ...]] = ('Авторизация',)

    @modify(
        status_code=HTTPStatus.OK,
        tags=['Авторизация'],
        summary='Получить JWT токены (Login)',
        extra_responses=[
            ResponseSpec(ErrorModel, status_code=HTTPStatus.UNAUTHORIZED),
        ],
    )
    def post(self, parsed_body: Body[LoginIn]) -> TokensOut:
        """Аутентификация пользователя по username и password."""
        user = authenticate(
            self.request,
            username=parsed_body.username,
            password=parsed_body.password,
        )
        if user is None:
            raise NotAuthenticatedError('Неверный логин или пароль.')

        if not isinstance(user, User):
            raise NotAuthenticatedError('Ошибка аутентификации.')

        return self.generate_token_pair(user)


@final
class RefreshController(_TokenMixin, Controller[MsgspecSerializer]):
    """Контроллер для обновления токенов."""

    auth = None
    tags: ClassVar[tuple[str, ...]] = ('Авторизация',)

    @modify(
        status_code=HTTPStatus.OK,
        tags=['Авторизация'],
        summary='Обновить токены (Refresh)',
        extra_responses=[
            ResponseSpec(ErrorModel, status_code=HTTPStatus.UNAUTHORIZED),
        ],
    )
    def post(self, parsed_body: Body[RefreshIn]) -> TokensOut:
        """Обновление токенов по refresh-токену."""
        try:
            decoded: dict[str, Any] = jwt.decode(
                parsed_body.refresh,
                settings.SECRET_KEY,
                algorithms=[self.jwt_algorithm],
            )
        except jwt.PyJWTError as e:
            raise NotAuthenticatedError(
                'Недействительный или просроченный токен.',
            ) from e

        if decoded.get('extras', {}).get('type') != 'refresh':
            raise NotAuthenticatedError('Это не refresh токен')

        try:
            user = User.objects.get(pk=decoded['sub'])
        except User.DoesNotExist as e:
            raise NotAuthenticatedError('Пользователь не найден.') from e

        return self.generate_token_pair(user)
