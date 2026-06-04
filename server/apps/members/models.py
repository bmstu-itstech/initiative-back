from typing import Any, ClassVar, override

from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone

from server.apps.members.managers import ActiveManager

UNIQUE_ACTIVE_FIO = 'unique_active_fio'
UNIQUE_ACTIVE_TELEGRAM = 'unique_active_telegram'
UNIQUE_ACTIVE_DIRECTION_NAME = 'unique_active_direction_name'
UNIQUE_ACTIVE_DEPARTMENT_IN_DIRECTION = 'unique_active_department_in_direction'
UNIQUE_ACTIVE_POSITION_IN_DEPARTMENT = 'unique_active_position_in_department'
UNIQUE_ACTIVE_POSITION_IN_DIRECTION = 'unique_active_position_in_direction'
CHECK_LEADER_BELONGS_TO_ONE_UNIT = 'check_leader_belongs_to_one_unit'


class SoftDeleteModel(models.Model):
    """Абстрактная модель с поддержкой мягкого удаления."""  # noqa: RUF002

    deleted_at = models.DateTimeField(
        default=None,
        null=True,
        blank=True,
        verbose_name='Дата удаления',
    )

    objects = ActiveManager()
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
        self.deleted_at = timezone.now()
        self.save(update_fields=['deleted_at'])
        return (1, {self._meta.label: 1})

    def restore(self) -> None:
        """Восстановление записи."""
        self.deleted_at = None
        self.save(update_fields=['deleted_at'])


class Member(SoftDeleteModel):
    """Модель Активиста Студенческого совета."""

    GROUP_REGEX = r'^((((ИУ|ИБМ|МТ|СМ|БМТ|РЛ|Э|РК|ФН|Л|СГН|РКТ|АК|ПС|РТ|ЛТ|К|ЮР)[1-9]\d?)|(ЮР(\.ДК)?))(К)?[ИЦ]?-(((1[0-2])|(\d))((\d)|(\.\d\d+))([АМБ]?(В)?)))$'  # noqa: E501, RUF001
    TELEGRAM_REGEX = r'^[a-zA-Z0-9_]{5,32}$'

    first_name = models.CharField(max_length=64, verbose_name='Имя')
    last_name = models.CharField(max_length=64, verbose_name='Фамилия')
    patronymic = models.CharField(
        max_length=64,
        blank=True,
        verbose_name='Отчество',
    )

    group = models.CharField(
        max_length=32,
        validators=[RegexValidator(regex=GROUP_REGEX)],
        blank=True,
        verbose_name='Группа',
    )
    telegram = models.CharField(
        max_length=32,
        validators=[RegexValidator(regex=TELEGRAM_REGEX)],
        verbose_name='Telegram ник',
    )
    birth_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Дата рождения',
    )
    join_date = models.DateField(
        auto_now_add=True,
        verbose_name='Дата вступления',
    )

    departments: models.ManyToManyField[Any, Any] = models.ManyToManyField(
        'Department',
        related_name='members',
        blank=True,
        verbose_name='Отделы',
    )

    class Meta:
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(
                fields=['last_name', 'first_name', 'patronymic'],
                name=UNIQUE_ACTIVE_FIO,
                condition=models.Q(deleted_at__isnull=True),
                nulls_distinct=False,
            ),
            models.UniqueConstraint(
                fields=['telegram'],
                name=UNIQUE_ACTIVE_TELEGRAM,
                condition=models.Q(deleted_at__isnull=True),
            ),
        ]
        verbose_name = 'Активист'
        verbose_name_plural = 'Активисты'

    @override
    def __str__(self) -> str:
        """Строковое представление активиста."""
        parts = [self.last_name, self.first_name]
        if self.patronymic:
            parts.append(self.patronymic)
        return ' '.join(parts)


class Direction(SoftDeleteModel):
    """Модель Направления."""

    name = models.CharField(max_length=128, verbose_name='Название')

    class Meta:
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(
                fields=['name'],
                name=UNIQUE_ACTIVE_DIRECTION_NAME,
                condition=models.Q(deleted_at__isnull=True),
            ),
        ]
        verbose_name = 'Направление'
        verbose_name_plural = 'Направления'

    @override
    def __str__(self) -> str:
        """Строковое представление направления."""
        return self.name


class Department(SoftDeleteModel):
    """Модель Отдела внутри Направления."""

    name = models.CharField(max_length=128, verbose_name='Название')
    direction = models.ForeignKey(
        Direction,
        on_delete=models.CASCADE,
        related_name='departments',
        db_index=True,
        verbose_name='Направление',
    )

    class Meta:
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(
                fields=['name', 'direction'],
                name=UNIQUE_ACTIVE_DEPARTMENT_IN_DIRECTION,
                condition=models.Q(deleted_at__isnull=True),
            ),
        ]
        verbose_name = 'Отдел'
        verbose_name_plural = 'Отделы'

    @override
    def __str__(self) -> str:
        """Строковое представление отдела."""
        return f'{self.name} ({self.direction.name})'


class Leader(SoftDeleteModel):
    """Модель Руководителя."""

    member = models.ForeignKey(
        Member,
        on_delete=models.CASCADE,
        related_name='leadership_roles',
        verbose_name='Активист',
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='leaders',
        db_index=True,
        verbose_name='Отдел',
    )
    direction = models.ForeignKey(
        Direction,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='leaders',
        db_index=True,
        verbose_name='Направление',
    )
    position = models.CharField(max_length=128, verbose_name='Должность')

    class Meta:
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(
                fields=['position', 'department'],
                name=UNIQUE_ACTIVE_POSITION_IN_DEPARTMENT,
                condition=models.Q(
                    deleted_at__isnull=True,
                    department__isnull=False,
                ),
            ),
            models.UniqueConstraint(
                fields=['position', 'direction'],
                name=UNIQUE_ACTIVE_POSITION_IN_DIRECTION,
                condition=models.Q(
                    deleted_at__isnull=True,
                    direction__isnull=False,
                ),
            ),
        ]
        verbose_name = 'Руководитель'
        verbose_name_plural = 'Руководители'

    @override
    def __str__(self) -> str:
        """Строковое представление руководителя."""
        unit = 'Без подразделения'
        if self.department:
            unit = self.department.name
        elif self.direction:
            unit = self.direction.name

        return f'{self.position} — {unit} ({self.member})'
