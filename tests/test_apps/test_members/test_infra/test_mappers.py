import pytest

from server.apps.members.infra.mappers import (
    DepartmentMapper,
    DirectionMapper,
    LeaderMapper,
    MemberMapper,
)
from server.apps.members.models import Department, Direction, Leader, Member


@pytest.mark.django_db
class TestMappers:
    """Тесты для преобразователей (Mappers) ORM моделей в DTO."""

    def test_direction_mapper(self, direction: Direction) -> None:
        """Проверка маппера направления."""
        mapper = DirectionMapper()
        result = mapper(direction)

        assert result.id == direction.pk
        assert result.name == direction.name

    def test_department_mapper(self, department: Department) -> None:
        """Проверка маппера отдела."""
        mapper = DepartmentMapper(direction_mapper=DirectionMapper())
        result = mapper(department)

        assert result.id == department.pk
        assert result.name == department.name
        assert result.direction.id == department.direction.pk

    def test_member_mapper(
        self,
        member: Member,
        department: Department,
    ) -> None:
        """Проверка маппера активиста."""
        member.departments.add(department)

        mapper = MemberMapper(
            department_mapper=DepartmentMapper(
                direction_mapper=DirectionMapper(),
            ),
        )
        result = mapper(member)

        assert result.id == member.pk
        assert result.first_name == member.first_name
        assert result.telegram == member.telegram
        assert result.join_date == member.join_date
        assert len(result.departments) == 1
        assert result.departments[0].id == department.pk

    def test_leader_mapper_with_department(self, leader: Leader) -> None:
        """Проверка маппера руководителя, который привязан к отделу."""
        mapper = LeaderMapper(
            member_mapper=MemberMapper(
                department_mapper=DepartmentMapper(
                    direction_mapper=DirectionMapper(),
                ),
            ),
            department_mapper=DepartmentMapper(
                direction_mapper=DirectionMapper(),
            ),
            direction_mapper=DirectionMapper(),
        )

        result = mapper(leader)

        assert result.id == leader.pk
        assert result.position == leader.position
        assert result.member.id == leader.member.pk
        assert result.department is not None
        assert result.department.id == leader.department.pk  # type: ignore[union-attr]
        assert result.direction is None

    def test_leader_mapper_with_direction(
        self,
        leader_direction: Leader,
    ) -> None:
        """Проверка маппера руководителя, который привязан к направлению."""
        mapper = LeaderMapper(
            member_mapper=MemberMapper(
                department_mapper=DepartmentMapper(
                    direction_mapper=DirectionMapper(),
                ),
            ),
            department_mapper=DepartmentMapper(
                direction_mapper=DirectionMapper(),
            ),
            direction_mapper=DirectionMapper(),
        )

        result = mapper(leader_direction)

        assert result.id == leader_direction.pk
        assert result.position == leader_direction.position
        assert result.direction is not None
        assert result.direction.id == leader_direction.direction.pk  # type: ignore[union-attr]
        assert result.department is None
