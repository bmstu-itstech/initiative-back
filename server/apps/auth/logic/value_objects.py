from typing import final

import msgspec


@final
class LoginIn(msgspec.Struct):
    """Payload для входа в систему (Login)."""

    username: str
    password: str


@final
class RefreshIn(msgspec.Struct):
    """Payload для обновления токена."""

    refresh: str


@final
class TokensOut(msgspec.Struct):
    """Ответ с парой токенов."""  # noqa: RUF002

    access_token: str
    refresh_token: str
