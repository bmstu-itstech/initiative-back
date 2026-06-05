from typing import Any, override

from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin, UserAdmin
from django.contrib.auth.models import Group, User
from django.db.models import QuerySet
from django.db.models.fields.related import ForeignKey, ManyToManyField
from django.forms.models import ModelChoiceField, ModelMultipleChoiceField
from django.http import HttpRequest

from .models import Department, Direction, Leader, Member

admin.site.unregister(User)
admin.site.unregister(Group)


@admin.register(User)
class CustomUserAdmin(UserAdmin[User]):
    """Панель управления пользователями системы (логины, пароли, группы)."""


@admin.register(Group)
class CustomGroupAdmin(GroupAdmin):
    """Панель управления группами (ролями: Viewer, Editor, Admin)."""


@admin.register(Direction)
class DirectionAdmin(admin.ModelAdmin[Direction]):
    """Админка для Направлений."""

    list_display = ('id', 'name', 'deleted_at')
    list_filter = ('deleted_at',)
    search_fields = ('name',)

    @override
    def get_queryset(self, request: HttpRequest) -> QuerySet[Direction]:
        """Используем all_objects, чтобы видеть удаленные записи."""
        return Direction.all_objects.all()


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin[Department]):
    """Админка для Отделов."""

    list_display = ('id', 'name', 'direction', 'deleted_at')
    list_filter = ('direction', 'deleted_at')
    search_fields = ('name', 'direction__name')
    list_select_related = ('direction',)

    @override
    def get_queryset(self, request: HttpRequest) -> QuerySet[Department]:
        """Используем all_objects, чтобы видеть удаленные записи."""
        return Department.all_objects.select_related('direction').all()


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin[Member]):
    """Админка для Активистов."""

    list_display = (
        'id',
        'first_name',
        'last_name',
        'group',
        'telegram',
        'get_departments',
        'deleted_at',
    )
    list_filter = ('group', 'deleted_at')
    search_fields = ('first_name', 'last_name', 'telegram')

    @override
    def get_queryset(self, request: HttpRequest) -> QuerySet[Member]:
        """Используем all_objects, чтобы видеть удаленные записи."""
        return Member.all_objects.prefetch_related('departments').all()

    def get_departments(self, obj: Member) -> str:
        """Отображение списка отделов активиста через запятую."""
        return ', '.join([dept.name for dept in obj.departments.all()])

    get_departments.short_description = 'Отделы'  # type: ignore[attr-defined]

    @override
    def formfield_for_manytomany(
        self,
        db_field: ManyToManyField[Any, Any],
        request: HttpRequest,
        **kwargs: Any,
    ) -> ModelMultipleChoiceField[Any] | None:
        """Защита от N+1 на странице создания/редактирования Активиста."""
        if db_field.name == 'departments':
            kwargs['queryset'] = Department.all_objects.select_related(
                'direction',
            ).all()

        return super().formfield_for_manytomany(db_field, request, **kwargs)


@admin.register(Leader)
class LeaderAdmin(admin.ModelAdmin[Leader]):
    """Админка для Руководителей."""

    list_display = ('id', 'member', 'position', 'get_unit', 'deleted_at')
    list_filter = ('deleted_at',)
    search_fields = ('position', 'member__first_name', 'member__last_name')
    list_select_related = ('member', 'department', 'direction')

    @override
    def get_queryset(self, request: HttpRequest) -> QuerySet[Leader]:
        """Используем all_objects, чтобы видеть удаленные записи."""
        return Leader.all_objects.select_related(
            'member',
            'department',
            'direction',
        ).all()

    def get_unit(self, obj: Leader) -> str:
        """Отображает, к какому подразделению привязан руководитель."""
        units = []
        if obj.department:
            units.append(f'Отдел: {obj.department.name}')
        if obj.direction:
            units.append(f'Направление: {obj.direction.name}')

        return ' и '.join(units) if units else '-'

    get_unit.short_description = 'Подразделение'  # type: ignore[attr-defined]

    @override
    def formfield_for_foreignkey(
        self,
        db_field: ForeignKey[Any, Any],
        request: HttpRequest,
        **kwargs: Any,
    ) -> ModelChoiceField[Any] | None:
        """Защита от N+1 на странице создания/редактирования Руководителя."""
        if db_field.name == 'department':
            kwargs['queryset'] = Department.all_objects.select_related(
                'direction',
            ).all()

        if db_field.name == 'member':
            kwargs['queryset'] = Member.all_objects.all()

        return super().formfield_for_foreignkey(db_field, request, **kwargs)
