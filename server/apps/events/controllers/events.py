from http import HTTPStatus

from django.http import HttpResponse
from dmr import Body, Query
from dmr.endpoint import validate
from dmr.metadata import ResponseSpec

from server.apps.auth.logic import permissions, roles
from server.apps.events.controllers.base import EventController
from server.apps.events.logic import queries, value_objects
from server.apps.events.logic.usecases import events
from server.common import value_objects as common_responses

EVENT_KEY = 'event_id'


class EventsController(EventController):
    """Список мероприятий и создание новых."""

    @validate(
        ResponseSpec(
            list[value_objects.EventListOut],
            status_code=HTTPStatus.OK,
        ),
    )
    @permissions.require_role([
        roles.Role.VIEWER,
        roles.Role.EDITOR,
        roles.Role.ADMIN,
    ])
    def get(
        self,
        parsed_query: Query[queries.EventFilterQuery],
    ) -> HttpResponse:
        """Возвращает страницу мероприятий без оргкомитетов."""
        return self.to_response(self.resolve(events.GetEventList)(parsed_query))

    @validate(
        ResponseSpec(value_objects.EventOut, status_code=HTTPStatus.CREATED),
        ResponseSpec(
            common_responses.ErrorResponse,
            status_code=HTTPStatus.BAD_REQUEST,
        ),
        ResponseSpec(
            common_responses.ErrorResponse,
            status_code=HTTPStatus.CONFLICT,
        ),
    )
    @permissions.require_role([roles.Role.EDITOR, roles.Role.ADMIN])
    def post(self, parsed_body: Body[value_objects.EventIn]) -> HttpResponse:
        """Создаёт мероприятие и оргкомитет."""
        return self.to_response(
            self.resolve(events.CreateEvent)(parsed_body),
            status_code=HTTPStatus.CREATED,
        )


class EventDetailController(EventController):
    """Чтение, обновление и мягкое удаление мероприятия."""

    @validate(
        ResponseSpec(value_objects.EventOut, status_code=HTTPStatus.OK),
        ResponseSpec(
            common_responses.ErrorResponse,
            status_code=HTTPStatus.NOT_FOUND,
        ),
    )
    @permissions.require_role([
        roles.Role.VIEWER,
        roles.Role.EDITOR,
        roles.Role.ADMIN,
    ])
    def get(self) -> HttpResponse:
        """Возвращает полную карточку мероприятия."""
        return self.to_response(
            self.resolve(events.GetEvent)(self.kwargs[EVENT_KEY]),
        )

    @validate(
        ResponseSpec(value_objects.EventOut, status_code=HTTPStatus.OK),
        ResponseSpec(
            common_responses.ErrorResponse,
            status_code=HTTPStatus.BAD_REQUEST,
        ),
        ResponseSpec(
            common_responses.ErrorResponse,
            status_code=HTTPStatus.CONFLICT,
        ),
        ResponseSpec(
            common_responses.ErrorResponse,
            status_code=HTTPStatus.NOT_FOUND,
        ),
    )
    @permissions.require_role([roles.Role.EDITOR, roles.Role.ADMIN])
    def put(self, parsed_body: Body[value_objects.EventIn]) -> HttpResponse:
        """Полностью заменяет мероприятие и оргкомитет."""
        return self.to_response(
            self.resolve(events.UpdateEvent)(
                self.kwargs[EVENT_KEY],
                parsed_body,
            ),
        )

    @validate(
        ResponseSpec(
            common_responses.SuccessResponse,
            status_code=HTTPStatus.OK,
        ),
        ResponseSpec(
            common_responses.ErrorResponse,
            status_code=HTTPStatus.NOT_FOUND,
        ),
    )
    @permissions.require_role([roles.Role.EDITOR, roles.Role.ADMIN])
    def delete(self) -> HttpResponse:
        """Мягко удаляет мероприятие без удаления назначений."""
        return self.to_response(
            self.resolve(events.DeleteEvent)(self.kwargs[EVENT_KEY]),
        )


class MemberEventsController(EventController):
    """Список назначений активиста в оргкомитеты мероприятий."""

    @validate(
        ResponseSpec(
            list[value_objects.MemberEventOut],
            status_code=HTTPStatus.OK,
        ),
        ResponseSpec(
            common_responses.ErrorResponse,
            status_code=HTTPStatus.NOT_FOUND,
        ),
    )
    @permissions.require_role([
        roles.Role.VIEWER,
        roles.Role.EDITOR,
        roles.Role.ADMIN,
    ])
    def get(self, parsed_query: Query[queries.EventListQuery]) -> HttpResponse:
        """Возвращает роли с краткими мероприятиями."""  # noqa: RUF002
        return self.to_response(
            self.resolve(events.GetMemberEvents)(
                self.kwargs['member_id'],
                parsed_query,
            ),
        )
