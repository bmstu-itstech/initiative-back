from typing import final

import attrs

from server.apps.members.infra.mappers import MemberMapper
from server.apps.members.infra.repository import MemberRepo
from server.apps.members.logic.queries import MemberFilterQuery
from server.apps.members.logic.value_objects import MemberIn, MemberOut


@final
@attrs.define(slots=True, frozen=True)
class GetMemberList:
    """Юзкейс получения списка активистов."""

    _repository: MemberRepo
    _mapper: MemberMapper

    def __call__(self, query: MemberFilterQuery) -> list[MemberOut]:
        """Выполняет логику."""
        return [self._mapper(m) for m in self._repository.get_list(query)]


@final
@attrs.define(slots=True, frozen=True)
class GetMember:
    """Юзкейс получения конкретного активиста."""

    _repository: MemberRepo
    _mapper: MemberMapper

    def __call__(self, member_id: int) -> MemberOut:
        """Выполняет логику."""
        return self._mapper(self._repository.get_by_id(member_id))


@final
@attrs.define(slots=True, frozen=True)
class GetMembersByDepartment:
    """Юзкейс получения активистов отдела."""

    _repository: MemberRepo
    _mapper: MemberMapper

    def __call__(self, department_id: int) -> list[MemberOut]:
        """Выполняет логику."""
        return [
            self._mapper(m)
            for m in self._repository.get_by_department(department_id)
        ]


@final
@attrs.define(slots=True, frozen=True)
class GetMembersByDirection:
    """Юзкейс получения активистов направления."""

    _repository: MemberRepo
    _mapper: MemberMapper

    def __call__(self, direction_id: int) -> list[MemberOut]:
        """Выполняет логику."""
        return [
            self._mapper(m)
            for m in self._repository.get_by_direction(direction_id)
        ]


@final
@attrs.define(slots=True, frozen=True)
class CreateMember:
    """Юзкейс создания активиста."""

    _repository: MemberRepo
    _mapper: MemberMapper

    def __call__(self, parsed_body: MemberIn) -> MemberOut:
        """Выполняет логику."""
        member = self._repository.create(parsed_body)
        return self._mapper(member)


@final
@attrs.define(slots=True, frozen=True)
class UpdateMember:
    """Юзкейс обновления активиста."""

    _repository: MemberRepo
    _mapper: MemberMapper

    def __call__(self, member_id: int, parsed_body: MemberIn) -> MemberOut:
        """Выполняет логику."""
        member = self._repository.get_by_id(member_id)
        updated_member = self._repository.update(member, parsed_body)
        return self._mapper(updated_member)


@final
@attrs.define(slots=True, frozen=True)
class DeleteMember:
    """Юзкейс удаления активиста."""

    _repository: MemberRepo

    def __call__(self, member_id: int) -> dict[str, str]:
        """Выполняет логику."""
        member = self._repository.get_by_id(member_id)
        self._repository.delete(member)
        return {'status': 'success', 'message': 'Member deleted (soft)'}
