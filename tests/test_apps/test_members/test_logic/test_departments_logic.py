import pytest

from server.apps.members.infra.mappers import DepartmentMapper, DirectionMapper
from server.apps.members.infra.repository import DepartmentRepo
from server.apps.members.logic.usecases.departments import CreateDepartment
from server.apps.members.logic.value_objects import DepartmentIn
from server.apps.members.models import Department, Direction


@pytest.mark.django_db
class TestDepartmentsLogic:
    """Тесты бизнес-логики для Отделов."""

    def test_create_department(
        self,
        direction: Direction,
        department_in: DepartmentIn,
    ) -> None:
        """Тест юзкейса создания отдела."""
        repo = DepartmentRepo()
        mapper = DepartmentMapper(direction_mapper=DirectionMapper())
        usecase = CreateDepartment(repository=repo, mapper=mapper)

        department_in.direction_id = direction.id
        department_out = usecase(parsed_body=department_in)

        assert department_out.id is not None
        assert department_out.name == department_in.name
        assert department_out.direction.id == direction.id
        assert Department.objects.filter(id=department_out.id).exists()
