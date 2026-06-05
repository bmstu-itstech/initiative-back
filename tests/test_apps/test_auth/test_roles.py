from server.apps.auth.logic.roles import Role


def test_all_roles() -> None:
    """Покрытие метода all_roles() в перечислении Role."""
    roles = Role.all_roles()

    assert len(roles) == 3
    assert 'Viewer' in roles
    assert 'Editor' in roles
    assert 'Admin' in roles
