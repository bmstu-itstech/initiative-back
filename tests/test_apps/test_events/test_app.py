import pytest
from django.apps import apps


def test_events_is_separate_app() -> None:
    """Мероприятия зарегистрированы отдельным приложением Django."""
    assert apps.is_installed('server.apps.events')
    event = apps.get_model('events', 'Event')
    organizer = apps.get_model('events', 'EventOrganizer')
    member = apps.get_model('members', 'Member')
    assert (
        bool(organizer._meta.get_field('event').related_model is event),  # noqa: SLF001
        bool(organizer._meta.get_field('member').related_model is member),  # noqa: SLF001
    ) == (
        True,
        True,
    )
    with pytest.raises(LookupError):
        apps.get_model('members', 'Event')
    with pytest.raises(LookupError):
        apps.get_model('members', 'EventOrganizer')
