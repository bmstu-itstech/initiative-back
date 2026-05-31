import pytest
from django.db import IntegrityError

from server.apps.members.models import Department, Direction, Leader, Member

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

    assert Member.objects.count() == 1
    assert Member.all_objects.count() == 1

    member.delete()
    member.refresh_from_db()
    assert member.is_deleted
    assert member.deleted_at is not None
    assert Member.objects.count() == 0
    assert Member.all_objects.count() == 1

    member.restore()
    member.refresh_from_db()
    assert not member.is_deleted
    assert member.deleted_at is None
    assert Member.objects.count() == 1


def test_hierarchy_str_representation() -> None:
    """Проверка строкового представления иерархии организации."""
    direction = Direction.objects.create(name='Информационные технологии')
    assert str(direction) == 'Информационные технологии'

    department = Department.objects.create(
        name='Отдел разработки',
        direction=direction,
    )
    assert str(department) == 'Отдел разработки (Информационные технологии)'

    member = Member.objects.create(
        first_name='Анна',
        last_name='Смирнова',
        telegram='anna_sm',
    )

    leader_dept = Leader.objects.create(
        member=member,
        department=department,
        position='Руководитель',
    )
    assert str(leader_dept) == 'Руководитель — Отдел разработки (Смирнова Анна)'

    leader_dir = Leader.objects.create(
        member=Member.objects.create(
            first_name='Илья',
            last_name='Ильин',
            telegram='ilya_il',
        ),
        direction=direction,
        position='Глава направления',
    )
    assert (
        str(leader_dir)
        == 'Глава направления — Информационные технологии (Ильин Илья)'
    )


def test_leader_constraints() -> None:
    """Проверка констрейнтов руководителя (уникальность должности)."""
    direction = Direction.objects.create(name='Волонтерский центр')
    member1 = Member.objects.create(
        first_name='А',  # noqa: RUF001
        last_name='Б',
        telegram='user123',
    )
    member2 = Member.objects.create(
        first_name='В',  # noqa: RUF001
        last_name='Г',
        telegram='user456',
    )

    Leader.objects.create(
        member=member1,
        direction=direction,
        position='Глава',
    )

    with pytest.raises(IntegrityError):
        Leader.objects.create(
            member=member2,
            direction=direction,
            position='Глава',
        )
