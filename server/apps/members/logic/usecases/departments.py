from typing import final

import attrs

from server.apps.members.infra.mappers import DepartmentMapper
from server.apps.members.infra.repository import DepartmentRepo
from server.apps.members.logic import exceptions
from server.apps.members.logic.value_objects import DepartmentIn, DepartmentOut


@final
@attrs.define(slots=True, frozen=True)
class GetDepartmentList:
    """Юзкейс получения списка отделов."""

    _repository: DepartmentRepo
    _mapper: DepartmentMapper

    def __call__(self) -> list[DepartmentOut]:
        """Выполняет логику."""
        return [self._mapper(d) for d in self._repository.get_all()]


@final
@attrs.define(slots=True, frozen=True)
class GetDepartment:
    """Юзкейс получения конкретного отдела."""

    _repository: DepartmentRepo
    _mapper: DepartmentMapper

    def __call__(self, department_id: int) -> DepartmentOut:
        """Выполняет логику."""
        return self._mapper(self._repository.get_by_id(department_id))


@final
@attrs.define(slots=True, frozen=True)
class CreateDepartment:
    """Юзкейс создания отдела."""

    _repository: DepartmentRepo
    _mapper: DepartmentMapper

    def __call__(self, parsed_body: DepartmentIn) -> DepartmentOut:
        """Выполняет логику."""
        department = self._repository.create(
            name=parsed_body.name,
            direction_id=parsed_body.direction_id,
        )
        return self._mapper(department)


@final
@attrs.define(slots=True, frozen=True)
class UpdateDepartment:
    """Юзкейс обновления отдела."""

    _repository: DepartmentRepo
    _mapper: DepartmentMapper

    def __call__(
        self,
        department_id: int,
        parsed_body: DepartmentIn,
    ) -> DepartmentOut:
        """Выполняет логику."""
        department = self._repository.get_by_id(department_id)
        updated_department = self._repository.update(
            department,
            name=parsed_body.name,
            direction_id=parsed_body.direction_id,
        )
        return self._mapper(updated_department)


@final
@attrs.define(slots=True, frozen=True)
class DeleteDepartment:
    """Юзкейс удаления отдела."""

    _repository: DepartmentRepo

    def __call__(self, department_id: int) -> dict[str, str]:
        """Выполняет логику."""
        try:
            department = self._repository.get_by_id(department_id)
            self._repository.delete(department)
        except exceptions.ObjectNotFoundError:
            pass
        return {'status': 'success', 'message': 'Department deleted (soft)'}
