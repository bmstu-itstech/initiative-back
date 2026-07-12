from typing import final

import attrs

from server.apps.members.infra.mappers import LeaderMapper
from server.apps.members.infra.repository import LeaderRepo
from server.apps.members.logic import exceptions
from server.apps.members.logic.value_objects import LeaderIn, LeaderOut


@final
@attrs.define(slots=True, frozen=True)
class GetLeaderList:
    """Юзкейс получения списка руководителей."""

    _repository: LeaderRepo
    _mapper: LeaderMapper

    def __call__(self) -> list[LeaderOut]:
        """Выполняет логику."""
        return [self._mapper(lead) for lead in self._repository.get_all()]


@final
@attrs.define(slots=True, frozen=True)
class GetLeader:
    """Юзкейс получения конкретного руководителя."""

    _repository: LeaderRepo
    _mapper: LeaderMapper

    def __call__(self, leader_id: int) -> LeaderOut:
        """Выполняет логику."""
        return self._mapper(self._repository.get_by_id(leader_id))


@final
@attrs.define(slots=True, frozen=True)
class CreateLeader:
    """Юзкейс назначения руководителя."""

    _repository: LeaderRepo
    _mapper: LeaderMapper

    def __call__(self, parsed_body: LeaderIn) -> LeaderOut:
        """Выполняет логику."""
        leader = self._repository.create(
            member_id=parsed_body.member_id,
            position=parsed_body.position,
            department_id=parsed_body.department_id,
            direction_id=parsed_body.direction_id,
        )
        return self._mapper(leader)


@final
@attrs.define(slots=True, frozen=True)
class UpdateLeader:
    """Юзкейс обновления руководителя."""

    _repository: LeaderRepo
    _mapper: LeaderMapper

    def __call__(self, leader_id: int, parsed_body: LeaderIn) -> LeaderOut:
        """Выполняет логику."""
        leader = self._repository.get_by_id(leader_id)
        updated_leader = self._repository.update(
            leader,
            member_id=parsed_body.member_id,
            position=parsed_body.position,
            department_id=parsed_body.department_id,
            direction_id=parsed_body.direction_id,
        )
        return self._mapper(updated_leader)


@final
@attrs.define(slots=True, frozen=True)
class DeleteLeader:
    """Юзкейс удаления руководителя."""

    _repository: LeaderRepo

    def __call__(self, leader_id: int) -> dict[str, str]:
        """Выполняет логику."""
        try:
            leader = self._repository.get_by_id(leader_id)
            self._repository.delete(leader)
        except exceptions.ObjectNotFoundError:
            pass
        return {'status': 'success', 'message': 'Leader role deleted (soft)'}
