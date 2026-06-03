import pytest

from server.apps.members.infra.mappers import (
    DepartmentMapper,
    DirectionMapper,
    LeaderMapper,
    MemberMapper,
)
from server.apps.members.infra.repository import LeaderRepo
from server.apps.members.logic.usecases.leaders import (
    CreateLeader,
    DeleteLeader,
    GetLeaderList,
    UpdateLeader,
)
from server.apps.members.logic.value_objects import LeaderIn
from server.apps.members.models import Department, Leader, Member


@pytest.mark.django_db
class TestLeadersLogic:
    """Тесты бизнес-логики для Руководителей."""

    def _get_mapper(self) -> LeaderMapper:
        """Вспомогательный метод, чтобы не дублировать создание маппера."""
        dep_mapper = DepartmentMapper(direction_mapper=DirectionMapper())
        return LeaderMapper(
            member_mapper=MemberMapper(department_mapper=dep_mapper),
            department_mapper=dep_mapper,
            direction_mapper=DirectionMapper(),
        )

    def test_create_leader(
        self,
        member: Member,
        department: Department,
        leader_in: LeaderIn,
    ) -> None:
        """Тест юзкейса создания руководителя."""
        repo = LeaderRepo()
        usecase = CreateLeader(repository=repo, mapper=self._get_mapper())

        leader_in.member_id = member.id
        leader_in.department_id = department.id
        leader_in.direction_id = None

        leader_out = usecase(parsed_body=leader_in)

        assert leader_out.id is not None
        assert leader_out.member.id == member.id
        assert Leader.objects.filter(id=leader_out.id).exists()

    def test_get_leader_list(self, leader: Leader) -> None:
        """Тест юзкейса получения списка руководителей."""
        repo = LeaderRepo()
        usecase = GetLeaderList(repository=repo, mapper=self._get_mapper())

        result = usecase()
        assert len(result) >= 1
        assert any(lead.id == leader.id for lead in result)

    def test_update_leader(self, leader: Leader, leader_in: LeaderIn) -> None:
        """Тест юзкейса обновления руководителя."""
        repo = LeaderRepo()
        usecase = UpdateLeader(repository=repo, mapper=self._get_mapper())

        leader_in.member_id = leader.member.id
        leader_in.position = 'Новая крутая должность'
        leader_in.department_id = (
            leader.department.id if leader.department else None
        )
        leader_in.direction_id = (
            leader.direction.id if leader.direction else None
        )

        updated_leader = usecase(leader_id=leader.id, parsed_body=leader_in)
        assert updated_leader.position == 'Новая крутая должность'

    def test_delete_leader(self, leader: Leader) -> None:
        """Тест юзкейса удаления руководителя."""
        repo = LeaderRepo()
        usecase = DeleteLeader(repository=repo)

        result = usecase(leader_id=leader.id)
        assert result['status'] == 'success'

        leader.refresh_from_db()
        assert leader.is_deleted is True
