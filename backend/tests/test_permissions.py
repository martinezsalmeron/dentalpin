"""Unit tests for RBAC permissions module."""

from app.core.auth.permissions import (
    ROLES,
    expand_permissions,
    get_role_permissions,
    has_permission,
    permission_matches,
)


class TestPermissionMatches:
    """Tests for permission_matches function."""

    def test_wildcard_matches_everything(self):
        """Wildcard '*' should match any permission."""
        assert permission_matches("clinical.patients.read", "*") is True
        assert permission_matches("inventory.items.write", "*") is True
        assert permission_matches("admin.users.write", "*") is True
        assert permission_matches("future.module.action", "*") is True

    def test_module_wildcard_matches_module_permissions(self):
        """Module wildcard 'module.*' should match all permissions in that module."""
        assert permission_matches("clinical.patients.read", "clinical.*") is True
        assert permission_matches("clinical.patients.write", "clinical.*") is True
        assert permission_matches("clinical.appointments.read", "clinical.*") is True

    def test_module_wildcard_does_not_match_other_modules(self):
        """Module wildcard should not match permissions from other modules."""
        assert permission_matches("inventory.items.read", "clinical.*") is False
        assert permission_matches("admin.users.write", "clinical.*") is False

    def test_exact_match(self):
        """Exact permission strings should match."""
        assert permission_matches("clinical.patients.read", "clinical.patients.read") is True
        assert permission_matches("clinical.patients.write", "clinical.patients.write") is True

    def test_exact_mismatch(self):
        """Different permission strings should not match."""
        assert permission_matches("clinical.patients.read", "clinical.patients.write") is False
        assert permission_matches("clinical.patients.read", "clinical.appointments.read") is False


class TestHasPermission:
    """Tests for has_permission function."""

    def test_admin_has_all_permissions(self):
        """Admin role should have all permissions via wildcard."""
        assert has_permission("admin", "clinical.patients.read") is True
        assert has_permission("admin", "clinical.patients.write") is True
        assert has_permission("admin", "admin.users.write") is True
        assert has_permission("admin", "future.module.action") is True

    def test_dentist_has_clinical_permissions(self):
        """Dentist role should have all clinical permissions."""
        assert has_permission("dentist", "clinical.patients.read") is True
        assert has_permission("dentist", "clinical.patients.write") is True
        assert has_permission("dentist", "clinical.appointments.read") is True
        assert has_permission("dentist", "clinical.appointments.write") is True

    def test_dentist_lacks_admin_permissions(self):
        """Dentist role should not have admin permissions."""
        assert has_permission("dentist", "admin.users.write") is False

    def test_hygienist_limited_permissions(self):
        """Hygienist should have limited clinical permissions."""
        assert has_permission("hygienist", "clinical.patients.read") is True
        assert has_permission("hygienist", "clinical.patients.write") is False
        assert has_permission("hygienist", "clinical.appointments.read") is True
        assert has_permission("hygienist", "clinical.appointments.write") is True

    def test_receptionist_permissions(self):
        """Receptionist should have patient and appointment permissions."""
        assert has_permission("receptionist", "clinical.patients.read") is True
        assert has_permission("receptionist", "clinical.patients.write") is True
        assert has_permission("receptionist", "clinical.appointments.read") is True
        assert has_permission("receptionist", "clinical.appointments.write") is True
        assert has_permission("receptionist", "admin.users.write") is False

    def test_unknown_role_has_no_permissions(self):
        """Unknown role should have no permissions."""
        assert has_permission("unknown_role", "clinical.patients.read") is False
        assert has_permission("", "clinical.patients.read") is False


class TestExpandPermissions:
    """Tests for expand_permissions function."""

    def test_wildcard_expands_to_all(self):
        """Wildcard '*' should expand to all available permissions."""
        all_perms = [
            "clinical.patients.read",
            "clinical.patients.write",
            "clinical.appointments.read",
            "clinical.appointments.write",
            "inventory.items.read",
        ]
        result = expand_permissions(["*"], all_perms)
        assert set(result) == set(all_perms)

    def test_module_wildcard_expands_to_module_perms(self):
        """Module wildcard should expand to all module permissions."""
        all_perms = [
            "clinical.patients.read",
            "clinical.patients.write",
            "clinical.appointments.read",
            "inventory.items.read",
        ]
        result = expand_permissions(["clinical.*"], all_perms)
        assert "clinical.patients.read" in result
        assert "clinical.patients.write" in result
        assert "clinical.appointments.read" in result
        assert "inventory.items.read" not in result

    def test_exact_permissions_preserved(self):
        """Exact permissions should be preserved in expansion."""
        all_perms = [
            "clinical.patients.read",
            "clinical.patients.write",
            "clinical.appointments.read",
        ]
        result = expand_permissions(["clinical.patients.read"], all_perms)
        assert result == ["clinical.patients.read"]

    def test_mixed_permissions_expand_correctly(self):
        """Mix of wildcards and exact permissions should expand correctly."""
        all_perms = [
            "clinical.patients.read",
            "clinical.patients.write",
            "clinical.appointments.read",
            "clinical.appointments.write",
        ]
        role_perms = ["clinical.patients.read", "clinical.appointments.*"]
        result = expand_permissions(role_perms, all_perms)
        assert "clinical.patients.read" in result
        assert "clinical.appointments.read" in result
        assert "clinical.appointments.write" in result
        # patients.write should NOT be in result
        assert "clinical.patients.write" not in result


class TestGetRolePermissions:
    """Tests for get_role_permissions function."""

    def test_known_roles_return_permissions(self):
        """Known roles should return their defined permissions."""
        for role in ROLES:
            perms = get_role_permissions(role)
            assert isinstance(perms, list)
            assert len(perms) > 0

    def test_unknown_role_returns_empty(self):
        """Unknown role should return empty list."""
        assert get_role_permissions("unknown") == []
        assert get_role_permissions("") == []

    def test_admin_has_wildcard(self):
        """Admin role should have wildcard permission."""
        perms = get_role_permissions("admin")
        assert "*" in perms


class TestRolesConstant:
    """Tests for ROLES constant."""

    def test_all_expected_roles_defined(self):
        """All expected roles should be defined."""
        expected_roles = {"admin", "dentist", "hygienist", "assistant", "receptionist"}
        assert expected_roles == set(ROLES)
