from http import HTTPStatus
from typing import ClassVar, override

from django.contrib.auth.models import User
from django.http import HttpResponse
from dmr import Controller, security
from dmr.endpoint import Endpoint
from dmr.metadata import ResponseSpec
from dmr.plugins.msgspec import MsgspecSerializer
from dmr.security.jwt import auth

from server.apps.events.logic import exceptions
from server.common.di import HasContainer
from server.common.value_objects import ErrorResponse


class EventController(HasContainer, Controller[MsgspecSerializer]):
    """Общая аутентификация и обработка прикладных ошибок мероприятий."""

    request: security.AuthenticatedHttpRequest[User]
    auth = (auth.JWTSyncAuth(),)
    responses: ClassVar[tuple[ResponseSpec, ...]] = (
        ResponseSpec(ErrorResponse, status_code=HTTPStatus.FORBIDDEN),
    )

    tags: ClassVar[tuple[str, ...]] = ('Мероприятия',)

    @override
    def handle_error(
        self,
        endpoint: Endpoint,
        controller: Controller[MsgspecSerializer],
        exc: Exception,
    ) -> HttpResponse:
        if isinstance(exc, exceptions.ObjectNotFoundError):
            return self.to_error(
                self.format_error(str(exc), error_type='not_found'),
                status_code=HTTPStatus.NOT_FOUND,
            )
        if isinstance(exc, exceptions.ObjectAlreadyExistsError):
            return self.to_error(
                self.format_error(
                    str(exc),
                    error_type='database_integrity_error',
                ),
                status_code=HTTPStatus.CONFLICT,
            )
        if isinstance(exc, exceptions.EventValidationError):
            return self.to_error(
                self.format_error(str(exc), error_type='validation_error'),
                status_code=HTTPStatus.BAD_REQUEST,
            )
        return super().handle_error(endpoint, controller, exc)
