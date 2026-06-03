# NOTE: simple layers go on top!

from collections.abc import Callable
from typing import Any

import punq


def _global_namespace() -> dict[str, Any]:
    from django.conf import LazySettings  # noqa: F401
    from django.core.cache import BaseCache  # noqa: F401

    return locals()  # noqa: WPS421


def _create_injector[Thing](
    container: punq.Container,
    localns: dict[str, Any],
) -> Callable[[Thing], Thing]:
    # We need to provide the same string names as we do in the definition.
    localns.pop('container')
    localns.update(_global_namespace())
    container.registrations._localns.update(localns)  # noqa: SLF001
    return lambda service: service


def _inject_django(container: punq.Container) -> None:
    from django.conf import LazySettings, settings

    # Django:
    container.register(
        LazySettings,
        instance=settings,
        scope=punq.Scope.singleton,
    )


def _inject_members(container: punq.Container) -> None:
    from server.apps.members.infra import mappers, repository
    from server.apps.members.logic.usecases import (
        departments,
        directions,
        leaders,
        members,
    )

    # Hacks to resolve annotations:
    inject = _create_injector(container, locals())  # noqa: WPS421

    # Things to register:
    container.register(repository.DirectionRepo)
    container.register(mappers.DirectionMapper)
    container.register(repository.DepartmentRepo)
    container.register(mappers.DepartmentMapper)
    container.register(repository.LeaderRepo)
    container.register(mappers.LeaderMapper)
    container.register(repository.MemberRepo)
    container.register(mappers.MemberMapper)

    container.register(inject(directions.GetDirectionList))
    container.register(inject(directions.GetDirection))
    container.register(inject(directions.CreateDirection))
    container.register(inject(directions.UpdateDirection))
    container.register(inject(directions.DeleteDirection))

    container.register(inject(departments.GetDepartmentList))
    container.register(inject(departments.GetDepartment))
    container.register(inject(departments.CreateDepartment))
    container.register(inject(departments.UpdateDepartment))
    container.register(inject(departments.DeleteDepartment))

    container.register(inject(leaders.GetLeaderList))
    container.register(inject(leaders.GetLeader))
    container.register(inject(leaders.CreateLeader))
    container.register(inject(leaders.UpdateLeader))
    container.register(inject(leaders.DeleteLeader))

    container.register(inject(members.GetMemberList))
    container.register(inject(members.GetMember))
    container.register(inject(members.GetMembersByDepartment))
    container.register(inject(members.GetMembersByDirection))
    container.register(inject(members.CreateMember))
    container.register(inject(members.UpdateMember))
    container.register(inject(members.DeleteMember))


def populate_dependencies(container: punq.Container) -> punq.Container:
    """Populates dependencies for the container."""
    # Deps:
    _inject_django(container)
    # Apps:
    _inject_members(container)
    return container
