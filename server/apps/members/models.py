from typing import ClassVar, override

from django.core.validators import MinLengthValidator, RegexValidator
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
    telegram = models.CharField(
        max_length=32,
        validators=[MinLengthValidator(5)],
    )
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


class Direction(SoftDeleteModel):
    """Модель Направления."""

    name = models.CharField(max_length=128)

    class Meta:
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(
                fields=['name'],
                name='unique_active_direction_name',
                condition=models.Q(is_deleted=False),
            ),
        ]

    @override
    def __str__(self) -> str:
        """Строковое представление направления."""
        return self.name


class Department(SoftDeleteModel):
    """Модель Отдела внутри Направления."""

    name = models.CharField(max_length=128)
    direction = models.ForeignKey(
        Direction,
        on_delete=models.CASCADE,
        related_name='departments',
    )

    class Meta:
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(
                fields=['name', 'direction'],
                name='unique_active_department_in_direction',
                condition=models.Q(is_deleted=False),
            ),
        ]

    @override
    def __str__(self) -> str:
        """Строковое представление отдела."""
        return f'{self.name} ({self.direction.name})'


class Leader(SoftDeleteModel):
    """Модель Руководителя."""

    member = models.OneToOneField(
        Member,
        on_delete=models.CASCADE,
        related_name='leader_role',
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='leaders',
    )
    direction = models.ForeignKey(
        Direction,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='leaders',
    )
    position = models.CharField(max_length=128)

    class Meta:
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(
                fields=['position', 'department'],
                name='unique_active_position_in_department',
                condition=models.Q(is_deleted=False, department__isnull=False),
            ),
            models.UniqueConstraint(
                fields=['position', 'direction'],
                name='unique_active_position_in_direction',
                condition=models.Q(is_deleted=False, direction__isnull=False),
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(
                        department_id__isnull=False,
                        direction_id__isnull=True,
                    )
                    | models.Q(
                        department_id__isnull=True,
                        direction_id__isnull=False,
                    )
                ),
                name='check_leader_belongs_to_one_unit',
            ),
        ]

    @override
    def __str__(self) -> str:
        """Строковое представление руководителя."""
        unit = self.department.name if self.department else self.direction.name  # type: ignore[union-attr]
        return f'{self.position} — {unit} ({self.member})'
