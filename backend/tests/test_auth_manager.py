"""Unit tests for AuthResourceManager."""
import pytest
from unittest.mock import patch, MagicMock
from botocore.exceptions import ClientError

from database.schemas.user import UserItem
from tests.conftest import make_request, SAMPLE_USER_ITEM

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _cognito_client_error(code: str, message: str = "error") -> ClientError:
    return ClientError(
        {"Error": {"Code": code, "Message": message}},
        "operation_name",
    )


_PATCH_COGNITO = "managers.auth.AuthResourceManager._get_cognito_client"


def _build_manager(mock_cognito_fn=None):
    """Instantiate AuthResourceManager with mock db and cognito."""
    mock_db = MagicMock()

    # Default repo stubs
    mock_db.users.raw_get_item.return_value = None
    mock_db.users.get_by_id.return_value = None
    mock_db.users.find_by_email.return_value = None
    mock_db.users.create.return_value = None
    mock_db.users.raw_update_item.return_value = None
    mock_db.users.raw_scan.return_value = {"Items": [], "Count": 0}
    mock_db.org_invitations.raw_query.return_value = {"Items": []}
    mock_db.org_invitations.raw_update_item.return_value = None
    mock_db.organizations.raw_update_item.return_value = None
    mock_db.audit_logs.create.return_value = None

    from managers.auth.AuthResourceManager import AuthResourceManager
    mgr = AuthResourceManager(service_managers={"db": mock_db})

    # Replace the cognito client with a mock
    mock_cognito = MagicMock()
    mgr.cognito = mock_cognito

    return mgr, mock_cognito, mock_db


# ===========================================================================
# LOGIN TESTS
# ===========================================================================

class TestAuthLogin:

    @patch("managers.auth.AuthResourceManager.get_user_org_memberships", return_value=[])
    @patch("managers.auth.AuthResourceManager.is_super_admin", return_value=False)
    @patch("jwt.decode")
    def test_login_success(self, mock_jwt, mock_is_sa, mock_memberships):
        mgr, cognito, mock_db = _build_manager()

        cognito.initiate_auth.return_value = {
            "AuthenticationResult": {
                "IdToken": "fake-id-token",
                "AccessToken": "fake-access-token",
                "RefreshToken": "fake-refresh-token",
            }
        }
        mock_jwt.return_value = {
            "sub": "user-123",
            "given_name": "Test",
            "family_name": "User",
        }
        mock_db.users.raw_get_item.return_value = SAMPLE_USER_ITEM.copy()

        req = make_request(
            data={"action": "login", "email": "test@example.com", "password": "password123"},
            user_id=None,
        )
        resp = mgr.post(req)

        assert resp.success is True
        assert resp.status_code == 200
        assert resp.data["accessToken"] == "fake-id-token"
        assert resp.data["token"] == "fake-id-token"
        assert resp.data["refreshToken"] == "fake-refresh-token"
        assert "user" in resp.data

    def test_login_missing_fields(self):
        mgr, _, _ = _build_manager()

        req = make_request(data={"action": "login"}, user_id=None)
        resp = mgr.post(req)

        assert resp.success is False
        assert resp.status_code == 400
        assert "required" in resp.error.lower()

    def test_login_invalid_credentials(self):
        mgr, cognito, _ = _build_manager()
        cognito.initiate_auth.side_effect = _cognito_client_error("NotAuthorizedException")

        req = make_request(
            data={"action": "login", "email": "test@example.com", "password": "wrong"},
            user_id=None,
        )
        resp = mgr.post(req)

        assert resp.success is False
        assert resp.status_code == 401
        assert "Invalid email or password" in resp.error

    def test_login_new_password_challenge(self):
        mgr, cognito, _ = _build_manager()
        cognito.initiate_auth.return_value = {
            "ChallengeName": "NEW_PASSWORD_REQUIRED",
            "Session": "session-abc",
        }

        req = make_request(
            data={"action": "login", "email": "test@example.com", "password": "temppass1"},
            user_id=None,
        )
        resp = mgr.post(req)

        assert resp.success is True
        assert resp.data["challengeName"] == "NEW_PASSWORD_REQUIRED"
        assert resp.data["session"] == "session-abc"
        assert resp.data["email"] == "test@example.com"

    @patch("jwt.decode")
    def test_login_deactivated_user(self, mock_jwt):
        mgr, cognito, mock_db = _build_manager()

        cognito.initiate_auth.return_value = {
            "AuthenticationResult": {
                "IdToken": "fake-id-token",
                "AccessToken": "fake-access-token",
                "RefreshToken": "fake-refresh-token",
            }
        }
        mock_jwt.return_value = {"sub": "user-123"}

        deactivated = {**SAMPLE_USER_ITEM, "is_active": False}
        mock_db.users.raw_get_item.return_value = deactivated

        req = make_request(
            data={"action": "login", "email": "test@example.com", "password": "password123"},
            user_id=None,
        )
        resp = mgr.post(req)

        assert resp.success is False
        assert resp.status_code == 403
        assert "deactivated" in resp.error.lower()


# ===========================================================================
# REGISTER TESTS
# ===========================================================================

class TestAuthRegister:

    @patch("managers.auth.AuthResourceManager.get_user_org_memberships", return_value=[])
    @patch("managers.auth.AuthResourceManager.is_super_admin", return_value=False)
    @patch("managers.auth.AuthResourceManager.grant_role")
    def test_register_success(self, mock_grant, mock_is_sa, mock_memberships):
        mgr, cognito, mock_db = _build_manager()

        cognito.sign_up.return_value = {"UserSub": "new-user-sub"}
        cognito.admin_confirm_sign_up.return_value = {}
        cognito.admin_update_user_attributes.return_value = {}
        mock_db.users.raw_scan.return_value = {"Count": 0}

        req = make_request(
            data={
                "action": "register",
                "email": "new@example.com",
                "password": "StrongPass1!",
                "firstName": "New",
                "lastName": "User",
            },
            user_id=None,
        )
        resp = mgr.post(req)

        assert resp.success is True
        assert resp.status_code == 201
        assert "user" in resp.data

    def test_register_missing_fields(self):
        mgr, _, _ = _build_manager()

        req = make_request(data={"action": "register", "password": "StrongPass1!"}, user_id=None)
        resp = mgr.post(req)

        assert resp.success is False
        assert resp.status_code == 400

    def test_register_duplicate_email(self):
        mgr, cognito, _ = _build_manager()
        cognito.sign_up.side_effect = _cognito_client_error("UsernameExistsException")

        req = make_request(
            data={
                "action": "register",
                "email": "dup@example.com",
                "password": "StrongPass1!",
                "firstName": "Dup",
                "lastName": "User",
            },
            user_id=None,
        )
        resp = mgr.post(req)

        assert resp.success is False
        assert resp.status_code == 409
        assert "already registered" in resp.error.lower()

    def test_register_short_password(self):
        mgr, _, _ = _build_manager()

        req = make_request(
            data={
                "action": "register",
                "email": "short@example.com",
                "password": "short",
                "firstName": "Short",
                "lastName": "Pass",
            },
            user_id=None,
        )
        resp = mgr.post(req)

        assert resp.success is False
        assert resp.status_code == 400
        assert "8 characters" in resp.error


# ===========================================================================
# LOGOUT TESTS
# ===========================================================================

class TestAuthLogout:

    def test_logout_success(self):
        mgr, _, _ = _build_manager()

        req = make_request(data={"action": "logout"}, user_id="user-123")
        resp = mgr.post(req)

        assert resp.success is True
        assert resp.status_code == 200


# ===========================================================================
# REFRESH TESTS
# ===========================================================================

class TestAuthRefresh:

    def test_refresh_success(self):
        mgr, cognito, _ = _build_manager()
        cognito.initiate_auth.return_value = {
            "AuthenticationResult": {
                "IdToken": "new-id-token",
            }
        }

        req = make_request(data={"action": "refresh", "refreshToken": "old-refresh-token"}, user_id=None)
        resp = mgr.post(req)

        assert resp.success is True
        assert resp.data["token"] == "new-id-token"

    def test_refresh_missing_token(self):
        mgr, _, _ = _build_manager()

        req = make_request(data={"action": "refresh"}, user_id=None)
        resp = mgr.post(req)

        assert resp.success is False
        assert resp.status_code == 400
        assert "required" in resp.error.lower()


# ===========================================================================
# FORGOT PASSWORD TESTS
# ===========================================================================

class TestAuthForgotPassword:

    def test_forgot_password_success(self):
        mgr, cognito, _ = _build_manager()
        cognito.forgot_password.return_value = {}

        req = make_request(data={"action": "forgot_password", "email": "test@example.com"}, user_id=None)
        resp = mgr.post(req)

        assert resp.success is True
        assert resp.status_code == 200


# ===========================================================================
# RESET PASSWORD TESTS
# ===========================================================================

class TestAuthResetPassword:

    def test_reset_password_success(self):
        mgr, cognito, _ = _build_manager()
        cognito.confirm_forgot_password.return_value = {}

        req = make_request(
            data={
                "action": "reset_password",
                "email": "test@example.com",
                "code": "123456",
                "newPassword": "NewStrong1!",
            },
            user_id=None,
        )
        resp = mgr.post(req)

        assert resp.success is True
        assert resp.status_code == 200

    def test_reset_password_missing_fields(self):
        mgr, _, _ = _build_manager()

        req = make_request(
            data={"action": "reset_password", "email": "test@example.com"},
            user_id=None,
        )
        resp = mgr.post(req)

        assert resp.success is False
        assert resp.status_code == 400


# ===========================================================================
# ACTION ROUTING / NOT IMPLEMENTED TESTS
# ===========================================================================

class TestAuthActionRouting:

    def test_invalid_action_get(self):
        mgr, _, _ = _build_manager()

        req = make_request(data={"action": "nonexistent"}, user_id=None)
        resp = mgr.get(req)

        assert resp.success is False
        assert resp.status_code == 400

    def test_invalid_action_post(self):
        mgr, _, _ = _build_manager()

        req = make_request(data={"action": "nonexistent"}, user_id=None)
        resp = mgr.post(req)

        assert resp.success is False
        assert resp.status_code == 400

    def test_put_not_implemented(self):
        mgr, _, _ = _build_manager()

        req = make_request(data={}, user_id=None)
        resp = mgr.put(req)

        assert resp.success is False
        assert resp.status_code == 405

    def test_delete_not_implemented(self):
        mgr, _, _ = _build_manager()

        req = make_request(data={}, user_id=None)
        resp = mgr.delete(req)

        assert resp.success is False
        assert resp.status_code == 405
