import datetime
from typing import Annotated

import msgspec

GROUP_REGEX = r'^$|^((((ИУ|ИБМ|МТ|СМ|БМТ|РЛ|Э|РК|ФН|Л|СГН|РКТ|АК|ПС|РТ|ЛТ|К|ЮР)[1-9]\d?)|(ЮР(\.ДК)?))(К)?[ИЦ]?-(((1[0-2])|(\d))((\d)|(\.\d\d+))([АМБ]?(В)?)))$'  # noqa: E501, RUF001
TELEGRAM_REGEX = r'^[a-zA-Z0-9_]{5,32}$'


class ErrorDetail(msgspec.Struct):
    """Детальная информация об ошибке."""  # noqa: RUF002

    msg: str
    type: str


class ErrorResponse(msgspec.Struct):
    """Стандартная схема ответа с ошибкой."""  # noqa: RUF002

    detail: list[ErrorDetail]


class DirectionIn(msgspec.Struct):
    """Схема входящих данных для Направления."""

    name: Annotated[str, msgspec.Meta(min_length=1, max_length=128)]


class DirectionOut(msgspec.Struct):
    """Схема исходящих данных Направления."""

    id: int
    name: str


class DepartmentIn(msgspec.Struct):
    """Схема входящих данных для Отдела."""

    name: Annotated[str, msgspec.Meta(min_length=1, max_length=128)]
    direction_id: Annotated[int, msgspec.Meta(ge=1, le=2147483647)]


class DepartmentOut(msgspec.Struct):
    """Схема исходящих данных Отдела."""

    id: int
    name: str
    direction: DirectionOut


class MemberIn(msgspec.Struct):
    """Схема входящих данных для создания/обновления Активиста."""

    first_name: Annotated[str, msgspec.Meta(min_length=1, max_length=64)]
    last_name: Annotated[str, msgspec.Meta(min_length=1, max_length=64)]
    telegram: Annotated[
        str,
        msgspec.Meta(pattern=TELEGRAM_REGEX, max_length=32),
    ]

    patronymic: Annotated[str, msgspec.Meta(max_length=64)] = ''
    group: Annotated[str, msgspec.Meta(pattern=GROUP_REGEX, max_length=32)] = ''
    birth_date: datetime.date | None = None

    department_ids: list[Annotated[int, msgspec.Meta(ge=1, le=2147483647)]] = []


class MemberOut(msgspec.Struct):
    """Схема исходящих данных Активиста."""

    id: int
    first_name: str
    last_name: str
    patronymic: str
    telegram: str
    group: str
    birth_date: datetime.date | None
    join_date: datetime.date
    departments: list[DepartmentOut] = []


class LeaderIn(msgspec.Struct):
    """Схема входящих данных для Руководителя."""

    member_id: Annotated[int, msgspec.Meta(ge=1, le=2147483647)]
    position: Annotated[str, msgspec.Meta(min_length=1, max_length=128)]
    department_id: Annotated[int, msgspec.Meta(ge=1, le=2147483647)] | None = (
        None
    )
    direction_id: Annotated[int, msgspec.Meta(ge=1, le=2147483647)] | None = (
        None
    )


class LeaderOut(msgspec.Struct):
    """Схема исходящих данных Руководителя."""

    id: int
    position: str
    member: MemberOut
    department: DepartmentOut | None = None
    direction: DirectionOut | None = None
