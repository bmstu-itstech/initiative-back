from typing import ClassVar, override

from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone

from server.apps.members.managers import ActiveManager


class SoftDeleteModel(models.Model):
    """Абстрактная модель с поддержкой мягкого удаления."""  # noqa: RUF002

    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = ActiveManager()
    all_objects = models.Manager['SoftDeleteModel']()

    class Meta:
        abstract = True

    @override
    def delete(
        self,
        using: str | None = None,
        keep_parents: bool = False,
    ) -> tuple[int, dict[str, int]]:
        """Переопределение базового удаления для Soft Delete."""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at'])
        return (1, {self._meta.label: 1})

    def restore(self) -> None:
        """Вспомогательный метод для восстановления удаленной записи."""
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=['is_deleted', 'deleted_at'])


class Member(SoftDeleteModel):
    """Модель Активиста Студенческого совета."""

    GROUP_REGEX = r'^((((ИУ|ИБМ|МТ|СМ|БМТ|РЛ|Э|РК|ФН|Л|СГН|РКТ|АК|ПС|РТ|ЛТ|К|ЮР)[1-9]\d?)|(ЮР(\.ДК)?))(К)?[ИЦ]?-(((1[0-2])|(\d))((\d)|(\.\d\d+))([АМБ]?(В)?)))$'  # noqa: E501, RUF001

    first_name = models.CharField(max_length=64)
    last_name = models.CharField(max_length=64)
    patronymic = models.CharField(max_length=64, blank=True)

    group = models.CharField(
        max_length=32,
        validators=[RegexValidator(regex=GROUP_REGEX)],
        blank=True,
    )
    telegram = models.CharField(max_length=32)
    birth_date = models.DateField(null=True, blank=True)
    join_date = models.DateField(auto_now_add=True)

    class Meta:
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(
                fields=['last_name', 'first_name', 'patronymic'],
                name='unique_active_fio',
                condition=models.Q(is_deleted=False),
                nulls_distinct=False,
            ),
            models.UniqueConstraint(
                fields=['telegram'],
                name='unique_active_telegram',
                condition=models.Q(is_deleted=False),
            ),
        ]

    @override
    def __str__(self) -> str:
        """Строковое представление активиста."""
        parts = [self.last_name, self.first_name]
        if self.patronymic:
            parts.append(self.patronymic)
        return ' '.join(parts)
