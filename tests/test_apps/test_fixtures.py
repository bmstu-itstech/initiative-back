import pytest
from django.contrib.auth.models import User


@pytest.mark.django_db
class TestAuthFixtures:
    """Проверка корректной работы фикстур авторизации."""

    def test_tokens_generation(
        self,
        viewer_token: str,
        editor_token: str,
        superuser_token: str,
    ) -> None:
        """Проверка, что токены генерируются и выглядят как JWT."""
        for token in [viewer_token, editor_token, superuser_token]:
            assert isinstance(token, str)
            assert len(token.split('.')) == 3

    def test_auth_headers(
        self,
        auth_headers_viewer: dict[str, str],
        auth_headers_editor: dict[str, str],
        auth_headers_superuser: dict[str, str],
    ) -> None:
        """Проверка, что заголовки формируются верно."""
        for headers in [
            auth_headers_viewer,
            auth_headers_editor,
            auth_headers_superuser,
        ]:
            assert 'HTTP_AUTHORIZATION' in headers
            assert headers['HTTP_AUTHORIZATION'].startswith('Bearer ')

    def test_superuser_fixture(self, superuser: User) -> None:
        """Проверка создания суперюзера."""
        assert superuser.is_superuser is True
        assert superuser.username == 'admin_test'
