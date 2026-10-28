import datetime
from typing import Annotated

import msgspec

from server.apps.events.logic import constraints
from server.apps.members.logic.value_objects import MemberListOut


class EventOrganizerIn(msgspec.Struct):
    """Назначение активиста в оргкомитет."""

    member_id: Annotated[int, msgspec.Meta(ge=1, le=constraints.MAX_MEMBER_ID)]
    role: Annotated[
        str,
        msgspec.Meta(
            min_length=1,
            max_length=constraints.NAME_LENGTH,
            pattern=r'^[^\x00]*$',
        ),
    ]


class EventIn(msgspec.Struct):
    """Входные данные создания и полного обновления мероприятия."""

    name: Annotated[
        str,
        msgspec.Meta(
            min_length=1,
            max_length=constraints.NAME_LENGTH,
            pattern=r'^[^\x00]*$',
        ),
    ]
    starts_at: Annotated[datetime.datetime, msgspec.Meta(tz=True)]
    ends_at: Annotated[datetime.datetime, msgspec.Meta(tz=True)]
    description: Annotated[
        str,
        msgspec.Meta(
            max_length=constraints.DESCRIPTION_LENGTH,
            pattern=r'^[^\x00]*$',
        ),
    ] = ''
    locations: list[
        Annotated[
            str,
            msgspec.Meta(
                max_length=constraints.NAME_LENGTH,
                pattern=r'^[^\x00]*$',
            ),
        ]
    ] = []
    organizers: list[EventOrganizerIn] = []

    def __post_init__(self) -> None:
        """Проверяет согласованность дат мероприятия."""
        if self.starts_at > self.ends_at:
            raise ValueError('Начало мероприятия должно быть не позже конца.')


class EventListOut(msgspec.Struct):
    """Мероприятие без оргкомитета."""

    id: int
    name: str
    starts_at: datetime.datetime
    ends_at: datetime.datetime
    description: str
    locations: list[str]


class EventOrganizerOut(msgspec.Struct):
    """Назначение с краткими данными активиста."""  # noqa: RUF002

    member: MemberListOut
    role: str


class EventOut(EventListOut):
    """Полная карточка мероприятия."""

    organizers: list[EventOrganizerOut]


class MemberEventOut(msgspec.Struct):
    """Роль активиста с информацией о мероприятии."""  # noqa: RUF002

    event: EventListOut
    role: str
