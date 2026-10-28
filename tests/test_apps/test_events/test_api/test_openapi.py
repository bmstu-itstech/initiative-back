from http import HTTPStatus

import pytest
from django.test import Client

CSV_MIME = 'text/csv'
GET_METHOD = 'get'
CONTENT_KEY = 'content'
EXPORT_URL = '/api/events/export/'
JSON_MIME = 'application/json'


@pytest.mark.django_db
@pytest.mark.parametrize(
    ('path', 'method'),
    [
        ('/api/events/', GET_METHOD),
        ('/api/events/', 'post'),
        ('/api/events/{event_id}/', GET_METHOD),
        ('/api/events/{event_id}/', 'put'),
        ('/api/events/{event_id}/', 'delete'),
        (EXPORT_URL, GET_METHOD),
        ('/api/events/{event_id}/organizers/export/', GET_METHOD),
        ('/api/members/{member_id}/events/', GET_METHOD),
    ],
)
def test_openapi_describes_forbidden(
    client: Client,
    path: str,
    method: str,
) -> None:
    """Описывает отказ авторизованному пользователю без нужной роли."""
    schema = client.get('/docs/openapi.json/').json()
    responses = schema['paths'][path][method]['responses']
    assert str(HTTPStatus.FORBIDDEN.value) in responses


@pytest.mark.django_db
@pytest.mark.parametrize(
    'path',
    [
        EXPORT_URL,
        '/api/events/{event_id}/organizers/export/',
    ],
)
def test_openapi_describes_csv(client: Client, path: str) -> None:
    """Описывает CSV-выгрузку и JSON-ошибку."""
    schema = client.get('/docs/openapi.json/').json()
    responses = schema['paths'][path][GET_METHOD]['responses']
    assert (
        set(responses['200'][CONTENT_KEY]),
        responses['200'][CONTENT_KEY][CSV_MIME]['schema'],
        bool(JSON_MIME in responses['401'][CONTENT_KEY]),
        bool(CSV_MIME not in responses['401'][CONTENT_KEY]),
    ) == (
        {CSV_MIME},
        {'type': 'string', 'format': 'binary'},
        True,
        True,
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    'accept',
    [CSV_MIME, JSON_MIME, 'text/html'],
)
def test_csv_anonymous_error(client: Client, accept: str) -> None:
    """Возвращает ошибку авторизации при согласовании формата CSV."""
    response = client.get(EXPORT_URL, HTTP_ACCEPT=accept)
    assert (
        response.status_code,
        response['Content-Type'],
    ) == (
        HTTPStatus.UNAUTHORIZED,
        JSON_MIME,
    )
    assert response.json()['detail']


@pytest.mark.django_db
@pytest.mark.parametrize('accept', [CSV_MIME, JSON_MIME, 'text/html'])
def test_csv_success_headers(
    client: Client,
    auth_headers_viewer: dict[str, str],
    accept: str,
) -> None:
    """Возвращает CSV с согласованными заголовками и UTF-8 BOM."""  # noqa: RUF002
    response = client.get(
        EXPORT_URL,
        HTTP_ACCEPT=accept,
        HTTP_AUTHORIZATION=auth_headers_viewer['HTTP_AUTHORIZATION'],
    )
    assert (
        response.status_code,
        response['Content-Type'],
        response['Content-Disposition'],
        response.content[:3],
    ) == (
        200,
        'text/csv; charset=utf-8',
        'attachment; filename="events.csv"',
        b'\xef\xbb\xbf',
    )


@pytest.mark.django_db
def test_csv_not_found_as_json(
    client: Client,
    auth_headers_viewer: dict[str, str],
) -> None:
    """Отсутствующее мероприятие возвращает JSON-ошибку при Accept CSV."""
    response = client.get(
        '/api/events/2147483647/organizers/export/',
        HTTP_ACCEPT=CSV_MIME,
        HTTP_AUTHORIZATION=auth_headers_viewer['HTTP_AUTHORIZATION'],
    )
    assert (response.status_code, response['Content-Type']) == (
        404,
        JSON_MIME,
    )
