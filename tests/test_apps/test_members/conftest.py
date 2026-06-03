import random
from typing import cast, final

import pytest
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
