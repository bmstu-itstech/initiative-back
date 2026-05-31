from django.contrib import admin

from server.apps.members.models import Member


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin[Member]):
    """Админка для управления Активистами."""

    list_display = ('last_name', 'first_name', 'telegram', 'is_deleted')
    list_filter = ('is_deleted',)
    search_fields = ('last_name', 'first_name', 'telegram')
