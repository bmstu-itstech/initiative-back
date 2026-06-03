from dmr.routing import Router, path

from server.apps.members.controllers.departments import (
    DepartmentDetailController,
    DepartmentsController,
)
from server.apps.members.controllers.directions import (
    DirectionDetailController,
    DirectionsController,
)
from server.apps.members.controllers.leaders import (
    LeaderDetailController,
    LeadersController,
)
from server.apps.members.controllers.members import (
    DepartmentMembersController,
    DirectionMembersController,
    MemberDetailController,
    MembersController,
)

router = Router(
    prefix='',
    urls=[
        path('directions/', DirectionsController.as_view(), name='directions'),
        path(
            'directions/<int:direction_id>/',
            DirectionDetailController.as_view(),
            name='direction_detail',
        ),
        path(
            'departments/',
            DepartmentsController.as_view(),
            name='departments',
        ),
        path(
            'departments/<int:department_id>/',
            DepartmentDetailController.as_view(),
            name='department_detail',
        ),
        path('leaders/', LeadersController.as_view(), name='leaders'),
        path(
            'leaders/<int:leader_id>/',
            LeaderDetailController.as_view(),
            name='leader_detail',
        ),
        path(
            'department/<int:department_id>/',
            DepartmentMembersController.as_view(),
            name='department_members',
        ),
        path(
            'direction/<int:direction_id>/',
            DirectionMembersController.as_view(),
            name='direction_members',
        ),
        path('', MembersController.as_view(), name='members'),
        path(
            '<int:member_id>/',
            MemberDetailController.as_view(),
            name='member_detail',
        ),
    ],
)
