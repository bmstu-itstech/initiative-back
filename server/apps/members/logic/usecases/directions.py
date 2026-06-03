from typing import final

import attrs

from server.apps.members.infra.mappers import DirectionMapper
from server.apps.members.infra.repository import DirectionRepo
from server.apps.members.logic.value_objects import DirectionIn, DirectionOut


@final
@attrs.define(slots=True, frozen=True)
class GetDirectionList:
    """Юзкейс получения списка направлений."""

    _repository: DirectionRepo
    _mapper: DirectionMapper

    def __call__(self) -> list[DirectionOut]:
        """Выполняет логику."""
        return [self._mapper(d) for d in self._repository.get_all()]


@final
@attrs.define(slots=True, frozen=True)
class GetDirection:
    """Юзкейс получения конкретного направления."""

    _repository: DirectionRepo
    _mapper: DirectionMapper

    def __call__(self, direction_id: int) -> DirectionOut:
        """Выполняет логику."""
        return self._mapper(self._repository.get_by_id(direction_id))


@final
@attrs.define(slots=True, frozen=True)
class CreateDirection:
    """Юзкейс создания направления."""

    _repository: DirectionRepo
    _mapper: DirectionMapper

    def __call__(self, parsed_body: DirectionIn) -> DirectionOut:
        """Выполняет логику."""
        direction = self._repository.create(name=parsed_body.name)
        return self._mapper(direction)


@final
@attrs.define(slots=True, frozen=True)
class UpdateDirection:
    """Юзкейс обновления направления."""

    _repository: DirectionRepo
    _mapper: DirectionMapper

    def __call__(
        self,
        direction_id: int,
        parsed_body: DirectionIn,
    ) -> DirectionOut:
        """Выполняет логику."""
        direction = self._repository.get_by_id(direction_id)
        updated_direction = self._repository.update(direction, parsed_body.name)
        return self._mapper(updated_direction)


@final
@attrs.define(slots=True, frozen=True)
class DeleteDirection:
    """Юзкейс удаления направления."""

    _repository: DirectionRepo

    def __call__(self, direction_id: int) -> dict[str, str]:
        """Выполняет логику."""
        direction = self._repository.get_by_id(direction_id)
        self._repository.delete(direction)
        return {'status': 'success', 'message': 'Direction deleted (soft)'}
