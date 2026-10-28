from dmr.routing import Router, path

from server.apps.events.controllers.events import (
    EventDetailController,
    EventsController,
)
from server.apps.events.controllers.exports import (
    EventOrganizersExportController,
    EventsExportController,
)

router = Router(
    prefix='',
    urls=[
        path('export/', EventsExportController.as_view(), name='export'),
        path(
            '<int:event_id>/organizers/export/',
            EventOrganizersExportController.as_view(),
            name='organizers_export',
        ),
        path(
            '<int:event_id>/',
            EventDetailController.as_view(),
            name='detail',
        ),
        path('', EventsController.as_view(), name='list'),
    ],
)
