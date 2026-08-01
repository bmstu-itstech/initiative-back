import datetime

import pytest

from server.apps.members.infra.mappers import (
    DepartmentMapper,
    DirectionMapper,
    MemberMapper,
)
from server.apps.members.infra.repository import MemberRepo
from server.apps.members.logic.usecases.members import (
    CreateMember,
    UpdateMember,
)
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

        custom_join_date = datetime.date(2025, 1, 1)
        member_in.join_date = custom_join_date

        member_out = usecase(parsed_body=member_in)

        assert member_out.id is not None
        assert member_out.telegram == member_in.telegram
        assert member_out.join_date == custom_join_date
        assert len(member_out.departments) == 1
        assert Member.objects.filter(id=member_out.id).exists()

    def test_update_member_join_date(
        self,
        department: Department,
        member_in: MemberIn,
    ) -> None:
        """Тест обновления даты вступления активиста."""
        repo = MemberRepo()
        mapper = MemberMapper(
            department_mapper=DepartmentMapper(
                direction_mapper=DirectionMapper(),
            ),
        )
        create_usecase = CreateMember(repository=repo, mapper=mapper)
        update_usecase = UpdateMember(repository=repo, mapper=mapper)

        member_in.department_ids = [department.id]
        member_out = create_usecase(parsed_body=member_in)

        new_join_date = datetime.date(2026, 7, 31)
        member_in.join_date = new_join_date

        updated_member_out = update_usecase(
            member_id=member_out.id,
            parsed_body=member_in,
        )

        assert updated_member_out.id == member_out.id
        assert updated_member_out.join_date == new_join_date

        member_in_db = Member.objects.get(id=member_out.id)
        assert member_in_db.join_date == new_join_date
