from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone

class ActiveManager(models.Manager):
    """Кастомный менеджер для фильтрации удаленных записей."""
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)

class SoftDeleteModel(models.Model):
    """Абстрактная модель с поддержкой мягкого удаления."""
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = ActiveManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        """Переопределение базового удаления."""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at'])

    def restore(self):
        """Вспомогательный метод для восстановления."""
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=['is_deleted', 'deleted_at'])

class Member(SoftDeleteModel):
    """Модель Активиста Студенческого совета."""

    # Регулярное выражение экранировано для корректной работы в Python
    GROUP_REGEX = r'^((((ИУ|ИБМ|МТ|СМ|БМТ|РЛ|Э|РК|ФН|Л|СГН|РКТ|АК|ПС|РТ|ЛТ|К|ЮР)[1-9]\d?)|(ЮР(\.ДК)?))(К)?[ИЦ]?-(((1[0-2])|(\d))((\d)|(\.\d\d+))([АМБ]?(В)?)))$'

    first_name = models.CharField(max_length=64)
    last_name = models.CharField(max_length=64)
    patronymic = models.CharField(max_length=64, null=True, blank=True)

    group = models.CharField(
        max_length=32,
        validators=[RegexValidator(regex=GROUP_REGEX)],
        null=True,
        blank=True
    )
    # Убираем unique=True, так как уникальность регулируется через Meta
    telegram = models.CharField(max_length=32)
    birth_date = models.DateField(null=True, blank=True)
    join_date = models.DateField(auto_now_add=True)

    class Meta:
        constraints = [
            # 1. Уникальность ФИО только среди не удаленных пользователей.
            # nulls_distinct=False (PostgreSQL 15+) гарантирует, что два человека
            # без отчества (NULL) всё равно будут считаться дубликатами.
            models.UniqueConstraint(
                fields=['last_name', 'first_name', 'patronymic'],
                name='unique_active_fio',
                condition=models.Q(is_deleted=False),
                nulls_distinct=False
            ),
            # 2. Уникальность Telegram только среди не удаленных пользователей.
            models.UniqueConstraint(
                fields=['telegram'],
                name='unique_active_telegram',
                condition=models.Q(is_deleted=False)
            )
        ]

    def __str__(self):
        parts = [self.last_name, self.first_name]
        if self.patronymic:
            parts.append(self.patronymic)
        return " ".join(parts)
