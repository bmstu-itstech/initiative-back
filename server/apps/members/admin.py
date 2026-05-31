from django.contrib import admin

from server.apps.members.models import Department, Direction, Leader, Member


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin[Member]):
    """Админка для управления Активистами."""

    list_display = ('last_name', 'first_name', 'telegram', 'is_deleted')
    list_filter = ('is_deleted',)
    search_fields = ('last_name', 'first_name', 'telegram')


@admin.register(Direction)
class DirectionAdmin(admin.ModelAdmin[Direction]):
    """Админка для управления Направлениями."""

    list_display = ('name', 'is_deleted')


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin[Department]):
    """Админка для управления Отделами."""

    list_display = ('name', 'direction', 'is_deleted')
    list_filter = ('direction', 'is_deleted')


@admin.register(Leader)
class LeaderAdmin(admin.ModelAdmin[Leader]):
    """Админка для управления Руководителями."""

    list_display = (
        'member',
        'position',
        'department',
        'direction',
        'is_deleted',
    )
    list_filter = ('is_deleted', 'department', 'direction')
    search_fields = ('position', 'member__last_name')
