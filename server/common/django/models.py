from typing import override

from django.db import models
from django.utils import timezone

from server.common.django.managers import ActiveManager


class SoftDeleteModel(models.Model):
    """Абстрактная модель с поддержкой мягкого удаления."""  # noqa: RUF002

    deleted_at = models.DateTimeField(
        default=None,
        null=True,
        blank=True,
        verbose_name='Дата удаления',
    )

    objects = ActiveManager['SoftDeleteModel']()  # noqa: WPS110 — имя manager в Django
    all_objects = models.Manager['SoftDeleteModel']()

    class Meta:
        abstract = True

    @property
    def is_deleted(self) -> bool:
        """Свойство, вычисляемое на лету."""
        return self.deleted_at is not None

    @override
    def delete(
        self,
        using: str | None = None,
        keep_parents: bool = False,
    ) -> tuple[int, dict[str, int]]:
        """Переопределение базового удаления."""
        self.deleted_at = timezone.now()  # noqa: WPS601 — запись поля Django
        self.save(update_fields=['deleted_at'])
        return (1, {self._meta.label: 1})

    def restore(self) -> None:
        """Восстановление записи."""
        self.deleted_at = None  # noqa: WPS601 — запись поля Django
        self.save(update_fields=['deleted_at'])
