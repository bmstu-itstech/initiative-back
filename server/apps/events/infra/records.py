from datetime import date
from typing import NamedTuple


class OrganizerRecord(NamedTuple):
    """Проекция назначения и полей активиста для карточки мероприятия."""

    member_id: int
    role: str
    first_name: str
    last_name: str
    patronymic: str
    telegram: str
    group: str
    birth_date: date | None
    join_date: date


class OrganizerExportRecord(NamedTuple):
    """Проекция полей назначения для выгрузки оргкомитета."""

    member_id: int
    last_name: str
    first_name: str
    patronymic: str
    group: str
    role: str
