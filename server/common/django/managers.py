from typing import override

from django.db import models


class ActiveManager[ModelType: models.Model](models.Manager[ModelType]):
    """Выбирает только записи без отметки мягкого удаления."""

    @override
    def get_queryset(self) -> models.QuerySet[ModelType]:
        """Возвращает типизированный набор активных записей."""
        return super().get_queryset().filter(deleted_at__isnull=True)
