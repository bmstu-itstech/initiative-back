from typing import ClassVar, override

from django.contrib.postgres.fields import ArrayField
from django.db import models

from server.apps.events.logic import constraints
from server.common.django.models import SoftDeleteModel


class Event(SoftDeleteModel):
    """Мероприятие Студенческого совета."""

    name = models.CharField(
        max_length=constraints.NAME_LENGTH,
        verbose_name='Название',
    )
    starts_at = models.DateTimeField(verbose_name='Начало', db_index=True)
    ends_at = models.DateTimeField(verbose_name='Окончание')
    description = models.CharField(
        max_length=constraints.DESCRIPTION_LENGTH,
        blank=True,
        default='',
        verbose_name='Описание',
    )
    locations = ArrayField(
        models.CharField(max_length=constraints.NAME_LENGTH),
        default=list,
        blank=True,
        verbose_name='Места проведения',
    )

    class Meta:
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.CheckConstraint(
                condition=models.Q(starts_at__lte=models.F('ends_at')),
                name='event_start_before_end',
            ),
        ]
        verbose_name = 'Мероприятие'
        verbose_name_plural = 'Мероприятия'

    @override
    def __str__(self) -> str:
        """Возвращает название мероприятия."""
        return self.name


class EventOrganizer(models.Model):
    """Назначение активиста на строковую роль в оргкомитете."""

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='organizers',
        db_index=True,
        verbose_name='Мероприятие',
    )
    member = models.ForeignKey(
        'members.Member',
        on_delete=models.CASCADE,
        related_name='event_memberships',
        db_index=True,
        verbose_name='Активист',
    )
    role = models.CharField(
        max_length=constraints.NAME_LENGTH,
        verbose_name='Роль',
    )

    class Meta:
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(
                fields=['event', 'member', 'role'],
                name='unique_event_member_role',
            ),
        ]
        verbose_name = 'Член оргкомитета'
        verbose_name_plural = 'Члены оргкомитета'
