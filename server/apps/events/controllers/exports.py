from http import HTTPStatus

from django.http import HttpResponse
from dmr.endpoint import validate
from dmr.files import FileResponseSpec
from dmr.metadata import ResponseSpec

from server.apps.auth.logic import permissions, roles
from server.apps.events.controllers.csv import CSV_MIME, CsvController
from server.apps.events.logic.usecases import exports
from server.common import value_objects as common_responses


def _csv_response(csv_bytes: bytes, filename: str) -> HttpResponse:
    """Формирует ответ для скачивания CSV-файла."""
    response = HttpResponse(
        csv_bytes,
        content_type=f'{CSV_MIME}; charset=utf-8',
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


class EventsExportController(CsvController):
    """Выгрузка списка мероприятий без оргкомитетов."""

    @validate(
        FileResponseSpec(limit_to_content_types={CSV_MIME}),
        validate_responses=False,
    )
    @permissions.require_role([
        roles.Role.VIEWER,
        roles.Role.EDITOR,
        roles.Role.ADMIN,
    ])
    def get(self) -> HttpResponse:
        """Выгружает все активные мероприятия."""
        return _csv_response(
            self.resolve(exports.ExportEventsCsv)(),
            'events.csv',
        )


class EventOrganizersExportController(CsvController):
    """Выгрузка активных участников оргкомитета."""

    @validate(
        FileResponseSpec(limit_to_content_types={CSV_MIME}),
        ResponseSpec(
            common_responses.ErrorResponse,
            status_code=HTTPStatus.NOT_FOUND,
            limit_to_content_types={'application/json'},
        ),
        validate_responses=False,
    )
    @permissions.require_role([
        roles.Role.VIEWER,
        roles.Role.EDITOR,
        roles.Role.ADMIN,
    ])
    def get(self) -> HttpResponse:
        """Выгружает ID, ФИО, группу и роль каждого назначения."""
        return _csv_response(
            self.resolve(exports.ExportEventOrganizersCsv)(
                self.kwargs['event_id'],
            ),
            f'event_{self.kwargs["event_id"]}_organizers.csv',
        )
