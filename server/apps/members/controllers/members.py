import json
from collections.abc import Callable
from http import HTTPStatus
from typing import Any, final, override

from django.contrib.auth.models import User
from django.db import transaction
from django.http import HttpResponse
from dmr import Body, Controller, Query
from dmr.endpoint import Endpoint, validate
from dmr.errors import ErrorType
from dmr.files import FileResponseSpec
from dmr.metadata import ResponseSpec
from dmr.parsers import JsonParser, Parser
from dmr.plugins.msgspec import MsgspecSerializer
from dmr.renderers import FileRenderer, JsonRenderer, Renderer
from dmr.security import AuthenticatedHttpRequest
from dmr.security.jwt.auth import JWTSyncAuth

from server.apps.auth.logic.permissions import require_role
from server.apps.auth.logic.roles import Role
from server.apps.members.logic import exceptions
from server.apps.members.logic.queries import MemberFilterQuery
from server.apps.members.logic.usecases.directions import GetStructure
from server.apps.members.logic.usecases.members import (
    CreateMember,
    DeleteMember,
    ExportMembersCsv,
    GetMember,
    GetMemberList,
    GetMembersByDepartment,
    GetMembersByDirection,
    UpdateMember,
)
from server.apps.members.logic.value_objects import (
    ErrorResponse,
    MemberIn,
    MemberListOut,
    MemberOut,
    StructureDirectionOut,
    SuccessResponse,
)
from server.common.di import HasContainer


@final
class MembersStructureController(
    HasContainer,
    Controller[MsgspecSerializer],
):
    """Контроллер для получения древовидной структуры организации."""

    request: AuthenticatedHttpRequest[User]
    auth = (JWTSyncAuth(),)

    @validate(
        ResponseSpec(list[StructureDirectionOut], status_code=HTTPStatus.OK),
        tags=['Активисты'],
    )
    @require_role([Role.VIEWER, Role.EDITOR, Role.ADMIN])
    def get(self) -> HttpResponse:
        """
        Получение структуры.

        (Направления -> Отделы -> Руководители и Активисты).
        """
        result = self.resolve(GetStructure)()
        return self.to_response(result, status_code=HTTPStatus.OK)


@final
class MembersController(
    HasContainer,
    Controller[MsgspecSerializer],
):
    """Контроллер для списка активистов и создания новых."""

    request: AuthenticatedHttpRequest[User]
    auth = (JWTSyncAuth(),)

    @validate(
        ResponseSpec(list[MemberListOut], status_code=HTTPStatus.OK),
        tags=['Активисты'],
    )
    @require_role([Role.VIEWER, Role.EDITOR, Role.ADMIN])
    def get(self, parsed_query: Query[MemberFilterQuery]) -> HttpResponse:
        """Получение списка активистов с фильтрацией и пагинацией."""  # noqa: RUF002
        result = self.resolve(GetMemberList)(parsed_query)
        return self.to_response(result, status_code=HTTPStatus.OK)

    @validate(
        ResponseSpec(MemberOut, status_code=HTTPStatus.CREATED),
        ResponseSpec(ErrorResponse, status_code=HTTPStatus.BAD_REQUEST),
        ResponseSpec(ErrorResponse, status_code=HTTPStatus.CONFLICT),
        tags=['Активисты'],
    )
    @require_role([Role.EDITOR, Role.ADMIN])
    def post(self, parsed_body: Body[MemberIn]) -> HttpResponse:
        """Создание нового активиста."""
        result = self.resolve(CreateMember)(parsed_body)
        return self.to_response(result, status_code=HTTPStatus.CREATED)

    @override
    def handle_error(
        self,
        endpoint: Endpoint,
        controller: Controller[MsgspecSerializer],
        exc: Exception,
    ) -> HttpResponse:
        if isinstance(exc, exceptions.ObjectAlreadyExistsError):
            if transaction.get_connection().in_atomic_block:  # pragma: no cover
                transaction.set_rollback(True)  # pragma: no cover
            return self.to_error(
                self.format_error(
                    str(exc),
                    error_type='database_integrity_error',
                ),
                status_code=HTTPStatus.CONFLICT,
            )
        return super().handle_error(
            endpoint,
            controller,
            exc,
        )  # pragma: no cover


@final
class MemberDetailController(
    HasContainer,
    Controller[MsgspecSerializer],
):
    """Управление конкретным активистом."""

    request: AuthenticatedHttpRequest[User]
    auth = (JWTSyncAuth(),)

    @validate(
        ResponseSpec(MemberOut, status_code=HTTPStatus.OK),
        ResponseSpec(ErrorResponse, status_code=HTTPStatus.NOT_FOUND),
        tags=['Активисты'],
    )
    @require_role([Role.VIEWER, Role.EDITOR, Role.ADMIN])
    def get(self) -> HttpResponse:
        """Получение детальной информации об активисте."""  # noqa: RUF002
        result = self.resolve(GetMember)(self.kwargs['member_id'])
        return self.to_response(result, status_code=HTTPStatus.OK)

    @validate(
        ResponseSpec(MemberOut, status_code=HTTPStatus.OK),
        ResponseSpec(ErrorResponse, status_code=HTTPStatus.BAD_REQUEST),
        ResponseSpec(ErrorResponse, status_code=HTTPStatus.CONFLICT),
        ResponseSpec(ErrorResponse, status_code=HTTPStatus.NOT_FOUND),
        tags=['Активисты'],
    )
    @require_role([Role.EDITOR, Role.ADMIN])
    def put(self, parsed_body: Body[MemberIn]) -> HttpResponse:
        """Полное обновление данных активиста."""
        result = self.resolve(UpdateMember)(
            self.kwargs['member_id'],
            parsed_body,
        )
        return self.to_response(result, status_code=HTTPStatus.OK)

    @validate(
        ResponseSpec(SuccessResponse, status_code=HTTPStatus.OK),
        ResponseSpec(ErrorResponse, status_code=HTTPStatus.NOT_FOUND),
        tags=['Активисты'],
    )
    @require_role([Role.EDITOR, Role.ADMIN])
    def delete(self) -> HttpResponse:
        """Мягкое удаление активиста."""
        result = self.resolve(DeleteMember)(self.kwargs['member_id'])
        return self.to_response(result, status_code=HTTPStatus.OK)

    @override
    def handle_error(
        self,
        endpoint: Endpoint,
        controller: Controller[MsgspecSerializer],
        exc: Exception,
    ) -> HttpResponse:
        if isinstance(exc, exceptions.ObjectNotFoundError):
            if transaction.get_connection().in_atomic_block:  # pragma: no cover
                transaction.set_rollback(True)  # pragma: no cover
            return self.to_error(
                self.format_error(str(exc), error_type=ErrorType.not_found),
                status_code=HTTPStatus.NOT_FOUND,
            )
        if isinstance(exc, exceptions.ObjectAlreadyExistsError):
            if transaction.get_connection().in_atomic_block:  # pragma: no cover
                transaction.set_rollback(True)  # pragma: no cover
            return self.to_error(
                self.format_error(
                    str(exc),
                    error_type='database_integrity_error',
                ),
                status_code=HTTPStatus.CONFLICT,
            )
        return super().handle_error(
            endpoint,
            controller,
            exc,
        )  # pragma: no cover


@final
class DepartmentMembersController(
    HasContainer,
    Controller[MsgspecSerializer],
):
    """Контроллер для вывода активистов отдела."""

    request: AuthenticatedHttpRequest[User]
    auth = (JWTSyncAuth(),)

    @validate(
        ResponseSpec(list[MemberListOut], status_code=HTTPStatus.OK),
        ResponseSpec(ErrorResponse, status_code=HTTPStatus.NOT_FOUND),
        tags=['Активисты'],
    )
    @require_role([Role.VIEWER, Role.EDITOR, Role.ADMIN])
    def get(self) -> HttpResponse:
        """Вывод всех активистов конкретного отдела."""
        result = self.resolve(GetMembersByDepartment)(
            self.kwargs['department_id'],
        )
        return self.to_response(result, status_code=HTTPStatus.OK)


@final
class DirectionMembersController(
    HasContainer,
    Controller[MsgspecSerializer],
):
    """Контроллер для вывода активистов направления."""

    request: AuthenticatedHttpRequest[User]
    auth = (JWTSyncAuth(),)

    @validate(
        ResponseSpec(list[MemberListOut], status_code=HTTPStatus.OK),
        ResponseSpec(ErrorResponse, status_code=HTTPStatus.NOT_FOUND),
        tags=['Активисты'],
    )
    @require_role([Role.VIEWER, Role.EDITOR, Role.ADMIN])
    def get(self) -> HttpResponse:
        """Вывод всех активистов конкретного направления."""
        result = self.resolve(GetMembersByDirection)(
            self.kwargs['direction_id'],
        )
        return self.to_response(result, status_code=HTTPStatus.OK)


class FallbackHtmlRenderer(Renderer):
    """
    Архитектурный фикс (Content Negotiation) для браузерных запросов.

    Перехватывает заголовок Accept: text/html и отдает ошибки в
    виде JSON, предотвращая падение DMR с KeyError('text/html').
    """  # noqa: RUF002

    content_type = 'text/html'

    @override
    def render(
        self,
        to_serialize: Any,
        serializer_hook: Callable[[Any], Any],
    ) -> bytes:
        """Сериализует ответ в JSON для браузера."""
        return json.dumps(to_serialize, default=serializer_hook).encode('utf-8')

    @property
    @override
    def validation_parser(self) -> Parser:
        """Возвращает парсер для валидации сгенерированного ответа."""
        return JsonParser()


@final
class MemberExportController(
    HasContainer,
    Controller[MsgspecSerializer],
):
    """Контроллер для экспорта списка активистов в CSV."""

    request: AuthenticatedHttpRequest[User]
    auth = (JWTSyncAuth(),)

    @validate(
        FileResponseSpec(),
        tags=['Активисты'],
        renderers=[JsonRenderer(), FileRenderer(), FallbackHtmlRenderer()],
        validate_responses=False,
    )
    @require_role([Role.VIEWER, Role.EDITOR, Role.ADMIN])
    def get(self) -> HttpResponse:
        """Экспорт всех активистов в CSV формат."""
        csv_bytes = self.resolve(ExportMembersCsv)()

        response = HttpResponse(
            csv_bytes,
            content_type='text/csv; charset=utf-8',
        )
        response['Content-Disposition'] = 'attachment; filename="members.csv"'

        return response
