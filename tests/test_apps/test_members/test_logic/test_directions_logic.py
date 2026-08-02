import pytest

from server.apps.members.infra.mappers import (
    DirectionMapper,
    MemberListMapper,
    StructureDepartmentMapper,
    StructureDirectionMapper,
    StructureLeaderMapper,
)
from server.apps.members.infra.repository import DirectionRepo
from server.apps.members.logic.usecases.directions import (
    CreateDirection,
    GetDirectionList,
    GetStructure,
)
from server.apps.members.logic.value_objects import DirectionIn
from server.apps.members.models import Department, Direction, Leader


@pytest.mark.django_db
class TestDirectionsLogic:
    """Тесты бизнес-логики для Направлений."""

    def test_create_direction(self, direction_in: DirectionIn) -> None:
        """Тест юзкейса создания направления."""
        repo = DirectionRepo()
        mapper = DirectionMapper()
        usecase = CreateDirection(repository=repo, mapper=mapper)

        direction_out = usecase(parsed_body=direction_in)

        assert direction_out.id is not None
        assert direction_out.name == direction_in.name
        assert Direction.objects.filter(id=direction_out.id).exists()

    def test_get_directions_list(self, direction: Direction) -> None:
        """Тест юзкейса получения списка направлений."""
        repo = DirectionRepo()
        mapper = DirectionMapper()
        usecase = GetDirectionList(repository=repo, mapper=mapper)

        directions = usecase()

        assert len(directions) >= 1
        assert any(d.id == direction.id for d in directions)

    def test_get_structure(
        self,
        direction: Direction,
        department: Department,
        leader: Leader,
    ) -> None:
        """Тест юзкейса получения полной структуры."""
        repo = DirectionRepo()
        member_list_mapper = MemberListMapper()
        structure_leader_mapper = StructureLeaderMapper(
            member_mapper=member_list_mapper,
        )
        structure_department_mapper = StructureDepartmentMapper(
            leader_mapper=structure_leader_mapper,
            member_mapper=member_list_mapper,
        )
        mapper = StructureDirectionMapper(
            leader_mapper=structure_leader_mapper,
            department_mapper=structure_department_mapper,
        )
        usecase = GetStructure(repository=repo, mapper=mapper)

        structure = usecase()

        assert len(structure) >= 1
        assert any(d.id == direction.id for d in structure)
