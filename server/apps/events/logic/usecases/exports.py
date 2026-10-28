import csv
import io
from typing import final

import attrs
import msgspec

from server.apps.events.infra import mappers
from server.apps.events.infra.repository import EventRepo
from server.apps.events.logic.export_rows import (
    EventExportRow,
    EventOrganizerExportRow,
)


def _export_csv[Row: msgspec.Struct](
    rows: list[Row],
    row_type: type[Row],
) -> bytes:
    """Формирует CSV с заголовком, разделителем и UTF-8 BOM."""  # noqa: RUF002
    buffer = io.StringIO()
    writer = csv.DictWriter(
        buffer,
        fieldnames=[field.name for field in msgspec.structs.fields(row_type)],
        delimiter=';',
    )
    writer.writeheader()
    for row in rows:
        writer.writerow({
            key: _csv_cell(cell)
            for key, cell in msgspec.structs.asdict(row).items()
        })
    return buffer.getvalue().encode('utf-8-sig')


def _csv_cell(cell: object) -> object:
    """Экранирует строки, интерпретируемые таблицами как формулы."""
    if isinstance(cell, str) and cell.startswith((
        '=',
        '+',
        '-',
        '@',
        '\t',
        '\r',
        '\n',
    )):
        return f"'{cell}"
    return cell


@final
@attrs.define(slots=True, frozen=True)
class ExportEventsCsv:
    """Выгружает все активные мероприятия в CSV."""

    _repository: EventRepo
    _mapper: mappers.EventExportMapper

    def __call__(self) -> bytes:
        """Возвращает CSV без оргкомитетов и пагинации."""
        return _export_csv(
            [
                self._mapper(event)
                for event in self._repository.get_for_export()
            ],
            EventExportRow,
        )


@final
@attrs.define(slots=True, frozen=True)
class ExportEventOrganizersCsv:
    """Выгружает оргкомитет конкретного мероприятия в CSV."""

    _repository: EventRepo
    _mapper: mappers.EventOrganizerExportMapper

    def __call__(self, event_id: int) -> bytes:
        """Возвращает CSV активных участников оргкомитета."""
        return _export_csv(
            [
                self._mapper(organizer)
                for organizer in self._repository.get_organizers_for_export(
                    event_id,
                )
            ],
            EventOrganizerExportRow,
        )
