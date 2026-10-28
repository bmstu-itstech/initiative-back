import msgspec


class EventExportRow(msgspec.Struct):
    """Строка экспорта мероприятия без оргкомитета."""

    id: int
    name: str
    starts_at: str
    ends_at: str
    description: str
    locations: str


class EventOrganizerExportRow(msgspec.Struct):
    """Строка экспорта назначения в оргкомитете."""

    id: int
    full_name: str
    group: str
    role: str
