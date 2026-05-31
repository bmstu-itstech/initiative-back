import pytest

from server.apps.members.models import Member

pytestmark = pytest.mark.django_db


def test_member_str_representation() -> None:
    """Проверка строкового представления активиста (с отчеством и без)."""  # noqa: RUF002
    member_full = Member.objects.create(
        first_name='Иван',
        last_name='Иванов',
        patronymic='Иванович',
        telegram='ivan_ivanov',
        group='ИУ5-11Б',  # noqa: RUF001
    )
    assert str(member_full) == 'Иванов Иван Иванович'

    member_short = Member.objects.create(
        first_name='Петр',
        last_name='Петров',
        telegram='petr_petrov',
    )
    assert str(member_short) == 'Петров Петр'


def test_soft_delete_and_restore() -> None:
    """Проверка механизма мягкого удаления и восстановления."""
    member = Member.objects.create(
        first_name='Алексей',
        last_name='Смирнов',
        telegram='alex_smirnov',
    )

    # Изначально активист виден в обоих менеджерах
    assert Member.objects.count() == 1
    assert Member.all_objects.count() == 1

    # Удаляем (Soft Delete)
    member.delete()
    member.refresh_from_db()
    assert member.is_deleted
    assert member.deleted_at is not None

    # ActiveManager (objects) должен скрыть запись
    assert Member.objects.count() == 0
    # Базовый менеджер (all_objects) всё еще должен её видеть
    assert Member.all_objects.count() == 1

    # Восстанавливаем
    member.restore()
    member.refresh_from_db()
    assert not member.is_deleted
    assert member.deleted_at is None
    assert Member.objects.count() == 1
