import pytest
from django.contrib.auth.models import User

from server.apps.members.logic.value_objects import (
    DepartmentIn,
    DirectionIn,
    LeaderIn,
    MemberIn,
)
from server.apps.members.models import Department, Direction, Leader, Member


@pytest.mark.django_db
class TestFactoriesAndFixtures:
    """Осмысленные тесты для проверки работоспособности генераторов данных."""

    def test_member_in_factory(self, member_in: MemberIn) -> None:
        """Проверка генерации DTO активиста (включая кастомную группу)."""
        assert isinstance(member_in, MemberIn)
        assert member_in.first_name is not None
        assert member_in.group is not None
        assert member_in.group.startswith('ИУ')
        assert member_in.group.endswith('Б')

    def test_department_in_factory(self, department_in: DepartmentIn) -> None:
        """Проверка генерации DTO отдела."""
        assert isinstance(department_in, DepartmentIn)
        assert department_in.name is not None

    def test_direction_in_factory(self, direction_in: DirectionIn) -> None:
        """Проверка генерации DTO направления."""
        assert isinstance(direction_in, DirectionIn)
        assert direction_in.name is not None

    def test_leader_in_factory(self, leader_in: LeaderIn) -> None:
        """Проверка генерации DTO руководителя."""
        assert isinstance(leader_in, LeaderIn)
        assert leader_in.position is not None

    def test_db_fixtures_creation_leader_department(
        self,
        direction: Direction,
        department: Department,
        member: Member,
        leader: Leader,
    ) -> None:
        """Проверка генерации руководителя отдела."""
        assert direction.id is not None
        assert department.id is not None
        assert member.id is not None
        assert leader.id is not None
        assert department.direction.id == direction.id
        assert leader.member.id == member.id

    def test_db_fixtures_creation_leader_direction(
        self,
        leader_direction: Leader,
    ) -> None:
        """Проверка генерации руководителя направления."""
        assert leader_direction.id is not None
        assert leader_direction.member.id is not None
        assert leader_direction.direction is not None

    def test_roles_fixtures(
        self,
        viewer_user: User,
        editor_user: User,
        superuser: User,
    ) -> None:
        """Проверка корректной выдачи групп и прав доступа пользователям."""
        assert viewer_user.groups.filter(name='Viewer').exists()
        assert editor_user.groups.filter(name='Editor').exists()

        assert superuser.is_superuser is True
        assert superuser.is_staff is True
