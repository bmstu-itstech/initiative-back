import pytest

from server.apps.members.infra.mappers import (
    DepartmentMapper,
    DirectionMapper,
    MemberMapper,
)
from server.apps.members.infra.repository import MemberRepo
from server.apps.members.logic.usecases.members import CreateMember
from server.apps.members.logic.value_objects import MemberIn
from server.apps.members.models import Department, Member


@pytest.mark.django_db
class TestMembersLogic:
    """Тесты бизнес-логики для Активистов."""

    def test_create_member(
        self,
        department: Department,
        member_in: MemberIn,
    ) -> None:
        """Тест юзкейса создания активиста."""
        repo = MemberRepo()
        mapper = MemberMapper(
            department_mapper=DepartmentMapper(
                direction_mapper=DirectionMapper(),
            ),
        )
        usecase = CreateMember(repository=repo, mapper=mapper)

        member_in.department_ids = [department.id]
        member_out = usecase(parsed_body=member_in)

        assert member_out.id is not None
        assert member_out.telegram == member_in.telegram
        assert len(member_out.departments) == 1
        assert Member.objects.filter(id=member_out.id).exists()
