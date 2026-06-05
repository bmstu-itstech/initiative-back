from enum import StrEnum, unique
from typing import final


@final
@unique
class Role(StrEnum):
    """
    Список базовых ролей в системе.

    Роли привязываются к стандартной модели django.contrib.auth.models.Group.
    """

    VIEWER = 'Viewer'
    EDITOR = 'Editor'
    ADMIN = 'Admin'

    @classmethod
    def all_roles(cls) -> list[str]:
        """Возвращает список всех доступных ролей (в виде строк)."""
        return [role.value for role in cls]
