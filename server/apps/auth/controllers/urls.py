from dmr.routing import Router, path

from server.apps.auth.controllers.jwt import LoginController, RefreshController

router = Router(
    'auth/',
    [
        path('login/', LoginController.as_view(), name='login'),
        path('refresh/', RefreshController.as_view(), name='refresh'),
    ],
)
