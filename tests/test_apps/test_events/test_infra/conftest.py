from datetime import UTC, datetime

import pytest

from server.apps.events.logic.value_objects import EventIn, EventOrganizerIn
from server.apps.members.models import Member

HOST_ROLE = 'Ведущий'


@pytest.fixture
def event_data(member: Member) -> EventIn:
    """Готовит входные данные мероприятия для проверки синхронизации."""
    start = datetime(2026, 10, 28, tzinfo=UTC)
    return EventIn(
        name='Встреча',
        starts_at=start,
        ends_at=start,
        organizers=[EventOrganizerIn(member_id=member.pk, role=HOST_ROLE)],
    )
