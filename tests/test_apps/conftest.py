import random
from typing import Any, cast, final

import pytest
from django.contrib.auth.models import Group, User
from django.test import Client
from django.urls import reverse
from faker import Faker
from polyfactory.factories.msgspec_factory import MsgspecFactory

from server.apps.members.logic.value_objects import (
    DepartmentIn,
    DirectionIn,
    LeaderIn,
    MemberIn,
)
from server.apps.members.models import Department, Direction, Leader, Member


@final
class DirectionInFactory(MsgspecFactory[DirectionIn]):
    """Фабрика для генерации входных данных для сущности Direction."""

    __check_model__ = True


@final
class DepartmentInFactory(MsgspecFactory[DepartmentIn]):
    """Фабрика для генерации входных данных для сущности Department."""

    __check_model__ = True


@final
class MemberInFactory(MsgspecFactory[MemberIn]):
    """Фабрика для генерации входных данных для сущности Member."""

    __check_model__ = True

    @classmethod
    def group(cls) -> str:
        """Generate a valid student group name matching the regex."""
        return f'ИУ5-{random.randint(1, 9)}{random.randint(1, 9)}Б'  # noqa: RUF001, S311


@final
class LeaderInFactory(MsgspecFactory[LeaderIn]):
    """Фабрика для генерации входных данных для сущности Leader."""

    __check_model__ = True


@pytest.fixture
def member_in() -> MemberIn:
    """Создает фейковые входные данные для сущности Member."""
    return MemberInFactory.build()


@pytest.fixture
def department_in() -> DepartmentIn:
    """Создает фейковые входные данные для сущности Department."""
    return DepartmentInFactory.build()


@pytest.fixture
def direction_in() -> DirectionIn:
    """Создает фейковые входные данные для сущности Direction."""
    return DirectionInFactory.build()


@pytest.fixture
def leader_in() -> LeaderIn:
    """Создает фейковые входные данные для сущности Leader."""
    return LeaderInFactory.build()


@pytest.fixture
def direction(faker: Faker) -> Direction:
    """Создает фейковую инстанцию сущности Direction в БД."""
    return cast(
        Direction,
        Direction.objects.create(name=faker.company()[:128]),
    )


@pytest.fixture
def department(faker: Faker, direction: Direction) -> Department:
    """Создает фейковую инстанцию сущности Department в БД."""
    return cast(
        Department,
        Department.objects.create(
            name=faker.department()[:128]
            if hasattr(faker, 'department')
            else faker.job()[:128],
            direction=direction,
        ),
    )


@pytest.fixture
def member(faker: Faker) -> Member:
    """Создает фейковую инстанцию сущности Member в БД."""
    return cast(
        Member,
        Member.objects.create(
            first_name=faker.first_name()[:64],
            last_name=faker.last_name()[:64],
            patronymic=faker.middle_name()[:64]
            if hasattr(faker, 'middle_name')
            else '',
            group=f'ИУ5-{random.randint(1, 9)}{random.randint(1, 9)}Б',  # noqa: S311, RUF001
            telegram=faker.user_name()[:32],
            birth_date=faker.date_of_birth(minimum_age=17, maximum_age=25),
        ),
    )


@pytest.fixture
def leader(faker: Faker, member: Member, department: Department) -> Leader:
    """Создает фейковую инстанцию сущности Leader в БД."""
    return cast(
        Leader,
        Leader.objects.create(
            member=member,
            position=faker.job()[:128],
            department=department,
        ),
    )


@pytest.fixture
def leader_direction(
    faker: Faker,
    member: Member,
    direction: Direction,
) -> Leader:
    """Создает фейковую инстанцию сущности Leader в БД."""
    return cast(
        Leader,
        Leader.objects.create(
            member=member,
            position=faker.job()[:128],
            direction=direction,
        ),
    )


@pytest.fixture
def viewer_user(db: Any) -> User:
    """Создает пользователя с ролью Viewer."""  # noqa: RUF002
    user = User.objects.create_user(
        username='viewer_test',
        password='password123',  # noqa: S106
    )
    group, _ = Group.objects.get_or_create(name='Viewer')
    user.groups.add(group)
    return user


@pytest.fixture
def editor_user(db: Any) -> User:
    """Создает пользователя с ролью Editor."""  # noqa: RUF002
    user = User.objects.create_user(
        username='editor_test',
        password='password123',  # noqa: S106
    )
    group, _ = Group.objects.get_or_create(name='Editor')
    user.groups.add(group)
    return user


@pytest.fixture
def viewer_token(client: Client, viewer_user: User) -> str:
    """Возвращает access_token для Viewer-а через API логина."""  # noqa: RUF002
    response = client.post(
        reverse('api:auth:login'),
        data={'username': 'viewer_test', 'password': 'password123'},
        content_type='application/json',
    )
    return cast(str, response.json()['access_token'])


@pytest.fixture
def editor_token(client: Client, editor_user: User) -> str:
    """Возвращает access_token для Editor-а через API логина."""  # noqa: RUF002
    response = client.post(
        reverse('api:auth:login'),
        data={'username': 'editor_test', 'password': 'password123'},
        content_type='application/json',
    )
    return cast(str, response.json()['access_token'])


@pytest.fixture
def auth_headers_viewer(viewer_token: str) -> dict[str, str]:
    """Заголовки для выполнения запросов от лица Viewer."""
    return {'HTTP_AUTHORIZATION': f'Bearer {viewer_token}'}


@pytest.fixture
def auth_headers_editor(editor_token: str) -> dict[str, str]:
    """Заголовки для выполнения запросов от лица Editor."""
    return {'HTTP_AUTHORIZATION': f'Bearer {editor_token}'}


@pytest.fixture
def superuser(db: Any) -> User:
    """Создает суперпользователя (is_superuser=True)."""
    return User.objects.create_superuser(
        username='admin_test',
        password='password123',  # noqa: S106
        email='admin@example.com',
    )


@pytest.fixture
def superuser_token(client: Client, superuser: User) -> str:
    """Возвращает access_token для суперпользователя."""
    response = client.post(
        reverse('api:auth:login'),
        data={'username': 'admin_test', 'password': 'password123'},
        content_type='application/json',
    )
    return cast(str, response.json()['access_token'])


@pytest.fixture
def auth_headers_superuser(superuser_token: str) -> dict[str, str]:
    """Заголовки для выполнения запросов от лица суперпользователя."""
    return {'HTTP_AUTHORIZATION': f'Bearer {superuser_token}'}
