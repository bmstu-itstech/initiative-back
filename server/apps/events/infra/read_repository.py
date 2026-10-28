from itertools import starmap

from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import QuerySet

from server.apps.events.infra.records import (
    OrganizerExportRecord,
    OrganizerRecord,
)
from server.apps.events.logic.exceptions import ObjectNotFoundError
from server.apps.events.logic.queries import EventFilterQuery, EventListQuery
from server.apps.events.models import Event, EventOrganizer
from server.apps.members.models import Member

SEARCH_SIMILARITY = 0.3
PRIMARY_KEY = 'id'
MEMBER_KEY = 'member_id'
ROLE_FIELD = 'role'


class EventReadRepo:
    """Читает мероприятия и проекции назначений без лишних ORM-моделей."""

    def get_list(self, query: EventFilterQuery) -> list[Event]:
        """Возвращает страницу активных мероприятий."""
        queryset = Event.objects.order_by(query.sort_by, PRIMARY_KEY)
        if query.search:
            queryset = queryset.annotate(
                similarity=TrigramSimilarity('name', query.search),
            ).filter(similarity__gt=SEARCH_SIMILARITY)
        return list(queryset[query.offset : query.offset + query.limit])

    def get_by_id(self, event_id: int) -> Event:
        """Загружает мероприятие без создания моделей оргкомитета."""
        try:
            return Event.objects.get(pk=event_id)
        except Event.DoesNotExist:
            raise ObjectNotFoundError('Мероприятие не найдено.') from None

    def get_organizers(self, event_id: int) -> list[OrganizerRecord]:
        """Читает только поля карточки, не создавая ORM-модели участников."""
        rows = (
            self
            ._organizers()
            .filter(event_id=event_id)
            .values_list(
                MEMBER_KEY,
                ROLE_FIELD,
                'member__first_name',
                'member__last_name',
                'member__patronymic',
                'member__telegram',
                'member__group',
                'member__birth_date',
                'member__join_date',
            )
        )
        return list(starmap(OrganizerRecord, rows))

    def get_organizers_for_export(
        self,
        event_id: int,
    ) -> list[OrganizerExportRecord]:
        """Читает поля CSV без загрузки остальных данных активиста."""
        if not Event.objects.filter(pk=event_id).exists():
            raise ObjectNotFoundError('Мероприятие не найдено.')
        rows = (
            self
            ._organizers()
            .filter(event_id=event_id)
            .values_list(
                MEMBER_KEY,
                'member__last_name',
                'member__first_name',
                'member__patronymic',
                'member__group',
                ROLE_FIELD,
            )
        )
        return list(starmap(OrganizerExportRecord, rows))

    def get_for_export(self) -> list[Event]:
        """Возвращает все активные мероприятия без оргкомитета."""
        return list(Event.objects.order_by('-starts_at', PRIMARY_KEY))

    def get_memberships(
        self,
        member_id: int,
        query: EventListQuery,
    ) -> list[EventOrganizer]:
        """Возвращает страницу назначений активного активиста."""
        if not Member.objects.filter(pk=member_id).exists():
            raise ObjectNotFoundError('Активист не найден.')
        queryset = (
            EventOrganizer.objects
            .filter(
                member_id=member_id,
                event__deleted_at__isnull=True,
            )
            .select_related('event')
            .order_by(
                '-event__starts_at'
                if query.sort_by.startswith('-')
                else f'event__{query.sort_by}',
                'event_id',
                PRIMARY_KEY,
            )
        )
        return list(queryset[query.offset : query.offset + query.limit])

    def _organizers(self) -> QuerySet[EventOrganizer]:
        """Фильтрует и сортирует назначения для типизированных проекций."""
        return EventOrganizer.objects.filter(
            member__deleted_at__isnull=True,
        ).order_by(MEMBER_KEY, ROLE_FIELD, PRIMARY_KEY)
