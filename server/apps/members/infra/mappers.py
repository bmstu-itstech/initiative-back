from typing import final

import attrs

from server.apps.members.logic.value_objects import (
    DepartmentOut,
    DirectionOut,
    LeaderOut,
    MemberExportRow,
    MemberListOut,
    MemberOut,
)
from server.apps.members.models import Department, Direction, Leader, Member


@final
@attrs.define(slots=True, frozen=True)
class DirectionMapper:
    """Преобразует модель Direction в DTO."""

    def __call__(self, direction: Direction) -> DirectionOut:
        """Выполняет преобразование."""
        return DirectionOut(
            id=direction.pk,
            name=direction.name,
        )


@final
@attrs.define(slots=True, frozen=True)
class DepartmentMapper:
    """Преобразует модель Department в DTO."""

    _direction_mapper: DirectionMapper

    def __call__(self, department: Department) -> DepartmentOut:
        """Выполняет преобразование."""
        return DepartmentOut(
            id=department.pk,
            name=department.name,
            direction=self._direction_mapper(department.direction),
        )


@final
@attrs.define(slots=True, frozen=True)
class MemberMapper:
    """Базовый маппер для Активиста."""

    _department_mapper: DepartmentMapper

    def __call__(self, member: Member) -> MemberOut:
        """Выполняет преобразование."""
        return MemberOut(
            id=member.pk,
            first_name=member.first_name,
            last_name=member.last_name,
            patronymic=member.patronymic or None,
            telegram=member.telegram,
            group=member.group or None,
            birth_date=member.birth_date,
            join_date=member.join_date,
            departments=[
                self._department_mapper(d) for d in member.departments.all()
            ],
        )


@final
@attrs.define(slots=True, frozen=True)
class MemberListMapper:
    """Маппер для Активиста в списке (без подгрузки отделов)."""

    def __call__(self, member: Member) -> MemberListOut:
        """Выполняет преобразование."""
        return MemberListOut(
            id=member.pk,
            first_name=member.first_name,
            last_name=member.last_name,
            patronymic=member.patronymic or None,
            telegram=member.telegram,
            group=member.group or None,
            birth_date=member.birth_date,
            join_date=member.join_date,
        )


@final
@attrs.define(slots=True, frozen=True)
class MemberExportMapper:
    """Маппер для подготовки данных активиста к экспорту."""

    def __call__(self, member: Member) -> MemberExportRow:
        """Выполняет преобразование модели в DTO экспорта."""
        return MemberExportRow(
            id=member.pk,
            last_name=member.last_name or '',
            first_name=member.first_name or '',
            patronymic=member.patronymic or '',
            telegram=member.telegram or '',
            group=member.group or '',
            birth_date=(
                member.birth_date.strftime('%Y-%m-%d')
                if member.birth_date is not None
                else ''
            ),
            join_date=member.join_date.strftime('%Y-%m-%d'),
        )


@final
@attrs.define(slots=True, frozen=True)
class LeaderMapper:
    """Преобразует модель Leader в DTO."""

    _member_mapper: MemberMapper
    _department_mapper: DepartmentMapper
    _direction_mapper: DirectionMapper

    def __call__(self, leader: Leader) -> LeaderOut:
        """Выполняет преобразование."""
        return LeaderOut(
            id=leader.pk,
            position=leader.position,
            member=self._member_mapper(leader.member),
            department=(
                self._department_mapper(leader.department)
                if leader.department
                else None
            ),
            direction=(
                self._direction_mapper(leader.direction)
                if leader.direction
                else None
            ),
        )
