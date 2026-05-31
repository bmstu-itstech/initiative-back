from typing import Any, override

from django.db import models


class ActiveManager(models.Manager['Member']):  # type: ignore[name-defined]
    """Кастомный менеджер для фильтрации удаленных записей."""

    @override
    def get_queryset(self) -> models.QuerySet[Any]:
        """Возвращает QuerySet только с активными (не удаленными) записями."""  # noqa: RUF002
        return super().get_queryset().filter(is_deleted=False)
