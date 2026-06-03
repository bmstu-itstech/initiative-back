from collections.abc import Callable
from functools import wraps
from typing import Any

from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from dmr.security import AuthenticatedHttpRequest

from server.apps.auth.logic.roles import Role


def require_role(
    allowed_roles: list[Role],
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Декоратор для проверки ролей пользователя.

    Принимает список допустимых ролей.
    Если пользователь не входит ни в одну из них (и не является суперюзером),
    выбрасывает PermissionDenied (HTTP 403).
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            request: AuthenticatedHttpRequest[User] = self.request
            user = request.user

            if user.is_superuser:
                return func(self, *args, **kwargs)

            user_groups = set(user.groups.values_list('name', flat=True))
            allowed_group_names = {role.value for role in allowed_roles}

            if user_groups & allowed_group_names:
                return func(self, *args, **kwargs)

            raise PermissionDenied(
                f'Для выполнения этого действия требуются права: '
                f'{", ".join(allowed_group_names)}',
            )

        return wrapper

    return decorator
