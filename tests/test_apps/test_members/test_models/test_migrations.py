import pytest
from django_test_migrations.migrator import Migrator


def test_migration_0001_initial(migrator: Migrator) -> None:
    """Тестируем самую первую миграцию (создание Member)."""
    old_state = migrator.apply_initial_migration(('members', None))
    with pytest.raises(LookupError):
        old_state.apps.get_model('members', 'Member')

    new_state = migrator.apply_tested_migration(('members', '0001_initial'))
    member_model = new_state.apps.get_model('members', 'Member')

    member = member_model.objects.create(
        first_name='Иван',
        last_name='Иванов',
        telegram='ivanov',
    )
    assert member.pk is not None


def test_migration_0002_hierarchy(migrator: Migrator) -> None:
    """Тестируем добавление иерархии (Direction, Department, Leader)."""
    old_state = migrator.apply_initial_migration(('members', '0001_initial'))

    with pytest.raises(LookupError):
        old_state.apps.get_model('members', 'Direction')
    with pytest.raises(LookupError):
        old_state.apps.get_model('members', 'Department')
    with pytest.raises(LookupError):
        old_state.apps.get_model('members', 'Leader')

    new_state = migrator.apply_tested_migration(
        (
            'members',
            '0002_alter_member_telegram_direction_department_leader_and_more',
        ),
    )

    direction_model = new_state.apps.get_model('members', 'Direction')
    department_model = new_state.apps.get_model('members', 'Department')
    leader_model = new_state.apps.get_model('members', 'Leader')
    member_model = new_state.apps.get_model(
        'members',
        'Member',
    )

    member = member_model.objects.create(
        first_name='Алексей',
        last_name='Смирнов',
        telegram='alex_smirnov',
    )

    direction = direction_model.objects.create(name='IT Направление')
    assert direction.pk is not None

    department = department_model.objects.create(
        name='Отдел Backend',
        direction_id=direction.pk,
    )
    assert department.pk is not None

    leader = leader_model.objects.create(
        member_id=member.pk,
        department_id=department.pk,
        position='Руководитель бэкенда',
    )
    assert leader.pk is not None


def test_migration_0003_pg_trgm(migrator: Migrator) -> None:
    """Тестируем установку расширения pg_trgm."""
    migrator.apply_initial_migration(
        (
            'members',
            '0002_alter_member_telegram_direction_department_leader_and_more',
        ),
    )
    migrator.apply_tested_migration(('members', '0003_add_pg_trgm'))


def test_migration_0004_m2m_departments(migrator: Migrator) -> None:
    """Тестируем добавление связи ManyToMany (departments) к Member."""
    old_state = migrator.apply_initial_migration((
        'members',
        '0003_add_pg_trgm',
    ))
    old_member_model = old_state.apps.get_model('members', 'Member')

    old_member = old_member_model.objects.create(
        first_name='Петр',
        last_name='Петров',
        telegram='petrov_tg',
    )
    with pytest.raises(AttributeError):
        _ = old_member.departments

    new_state = migrator.apply_tested_migration(
        ('members', '0004_member_departments_alter_member_telegram'),
    )
    new_member_model = new_state.apps.get_model('members', 'Member')
    direction_model = new_state.apps.get_model('members', 'Direction')
    department_model = new_state.apps.get_model('members', 'Department')

    direction = direction_model.objects.create(name='Медиа')
    department = department_model.objects.create(
        name='Дизайн',
        direction_id=direction.pk,
    )

    new_member = new_member_model.objects.get(pk=old_member.pk)
    new_member.departments.add(department)

    assert new_member.departments.count() == 1


def test_migration_0005_default_groups(migrator: Migrator) -> None:
    """Тестируем накатывание и откат миграции создания ролей (0005)."""
    migrator.apply_initial_migration(
        ('members', '0004_member_departments_alter_member_telegram'),
    )

    new_state = migrator.apply_tested_migration(
        ('members', '0005_create_default_groups'),
    )
    group_model = new_state.apps.get_model('auth', 'Group')
    assert group_model.objects.filter(name='Viewer').exists()
    assert group_model.objects.filter(name='Editor').exists()
    assert group_model.objects.filter(name='Admin').exists()

    reverted_state = migrator.apply_tested_migration(
        ('members', '0004_member_departments_alter_member_telegram'),
    )
    reverted_group_model = reverted_state.apps.get_model('auth', 'Group')

    assert not reverted_group_model.objects.filter(name='Viewer').exists()
    assert not reverted_group_model.objects.filter(name='Editor').exists()
    assert not reverted_group_model.objects.filter(name='Admin').exists()
