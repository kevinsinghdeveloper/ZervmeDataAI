"""Unit tests for repository layer — DynamoDB raw methods, __getattr__ forwarding,
entity wrapper repos, and DatabaseService factory."""
import pytest
from unittest.mock import MagicMock, patch, PropertyMock

from database.repositories.connectors.DynamoDBConnector import DynamoDBConnector, DynamoDBRepository
from database.repositories.user_repository import UserRepository
from database.repositories.user_role_repository import UserRoleRepository
from database.repositories.config_repository import ConfigRepository


# ===========================================================================
# DynamoDBRepository raw methods
# ===========================================================================

class TestDynamoDBRepositoryRawMethods:
    """Test raw_* passthrough methods on DynamoDBRepository."""

    @pytest.fixture
    def mock_connector(self):
        connector = MagicMock(spec=DynamoDBConnector)
        mock_table = MagicMock()
        connector.get_table.return_value = mock_table
        return connector, mock_table

    @pytest.fixture
    def repo(self, mock_connector):
        connector, _ = mock_connector
        return DynamoDBRepository(connector, "users")

    def test_raw_get_item(self, repo, mock_connector):
        _, mock_table = mock_connector
        mock_table.get_item.return_value = {"Item": {"id": "u1", "email": "a@b.com"}}

        result = repo.raw_get_item({"id": "u1"})

        mock_table.get_item.assert_called_once_with(Key={"id": "u1"})
        assert result == {"id": "u1", "email": "a@b.com"}

    def test_raw_get_item_not_found(self, repo, mock_connector):
        _, mock_table = mock_connector
        mock_table.get_item.return_value = {}

        result = repo.raw_get_item({"id": "missing"})
        assert result is None

    def test_raw_update_item(self, repo, mock_connector):
        _, mock_table = mock_connector
        mock_table.update_item.return_value = {"Attributes": {"id": "u1"}}

        result = repo.raw_update_item(
            Key={"id": "u1"},
            UpdateExpression="SET #n = :v",
            ExpressionAttributeNames={"#n": "name"},
            ExpressionAttributeValues={":v": "New Name"},
        )

        mock_table.update_item.assert_called_once()
        kwargs = mock_table.update_item.call_args[1]
        assert kwargs["Key"] == {"id": "u1"}
        assert kwargs["UpdateExpression"] == "SET #n = :v"

    def test_raw_delete_item(self, repo, mock_connector):
        _, mock_table = mock_connector

        repo.raw_delete_item(Key={"id": "u1"})

        mock_table.delete_item.assert_called_once_with(Key={"id": "u1"})

    def test_raw_query(self, repo, mock_connector):
        _, mock_table = mock_connector
        mock_table.query.return_value = {"Items": [{"id": "u1"}, {"id": "u2"}], "Count": 2}

        result = repo.raw_query(
            IndexName="OrgIdIndex",
            KeyConditionExpression="org_id = :oid",
        )

        mock_table.query.assert_called_once()
        assert result["Count"] == 2
        assert len(result["Items"]) == 2

    def test_raw_scan(self, repo, mock_connector):
        _, mock_table = mock_connector
        mock_table.scan.return_value = {"Items": [], "Count": 0}

        result = repo.raw_scan(Select="COUNT")

        mock_table.scan.assert_called_once_with(Select="COUNT")
        assert result["Count"] == 0

    def test_raw_scan_with_filter(self, repo, mock_connector):
        _, mock_table = mock_connector
        mock_table.scan.return_value = {"Items": [{"id": "u1"}], "Count": 1}

        result = repo.raw_scan(FilterExpression="status = :s", ExpressionAttributeValues={":s": "active"})

        mock_table.scan.assert_called_once()
        assert result["Count"] == 1


# ===========================================================================
# DynamoDBRepository CRUD methods
# ===========================================================================

class TestDynamoDBRepositoryCRUD:
    """Test standard CRUD methods on DynamoDBRepository."""

    @pytest.fixture
    def mock_connector(self):
        connector = MagicMock(spec=DynamoDBConnector)
        mock_table = MagicMock()
        connector.get_table.return_value = mock_table
        return connector, mock_table

    @pytest.fixture
    def repo(self, mock_connector):
        connector, _ = mock_connector
        return DynamoDBRepository(connector, "users")

    def test_get_by_id(self, repo, mock_connector):
        _, mock_table = mock_connector
        mock_table.get_item.return_value = {"Item": {"id": "u1", "email": "a@b.com"}}

        result = repo.get_by_id("u1")
        assert result == {"id": "u1", "email": "a@b.com"}

    def test_get_by_id_not_found(self, repo, mock_connector):
        _, mock_table = mock_connector
        mock_table.get_item.return_value = {}

        result = repo.get_by_id("missing")
        assert result is None

    def test_get_by_key(self, repo, mock_connector):
        _, mock_table = mock_connector
        mock_table.get_item.return_value = {"Item": {"org_id": "o1", "id": "p1"}}

        result = repo.get_by_key({"org_id": "o1", "id": "p1"})
        mock_table.get_item.assert_called_once_with(Key={"org_id": "o1", "id": "p1"})
        assert result is not None

    def test_create(self, repo, mock_connector):
        _, mock_table = mock_connector
        item = {"id": "u1", "email": "a@b.com"}

        result = repo.create(item)
        mock_table.put_item.assert_called_once_with(Item=item)
        assert result == item

    def test_upsert(self, repo, mock_connector):
        _, mock_table = mock_connector
        item = {"id": "u1", "email": "updated@b.com"}

        result = repo.upsert(item)
        mock_table.put_item.assert_called_once_with(Item=item)
        assert result == item

    def test_update(self, repo, mock_connector):
        _, mock_table = mock_connector
        mock_table.update_item.return_value = {"Attributes": {"id": "u1", "email": "new@b.com"}}

        result = repo.update("u1", {"email": "new@b.com"})
        mock_table.update_item.assert_called_once()
        assert result == {"id": "u1", "email": "new@b.com"}

    def test_update_empty_fields(self, repo, mock_connector):
        _, mock_table = mock_connector
        mock_table.get_item.return_value = {"Item": {"id": "u1"}}

        result = repo.update("u1", {})
        mock_table.update_item.assert_not_called()
        assert result == {"id": "u1"}

    def test_delete(self, repo, mock_connector):
        _, mock_table = mock_connector

        result = repo.delete("u1")
        mock_table.delete_item.assert_called_once_with(Key={"id": "u1"})
        assert result is True

    def test_delete_by_key(self, repo, mock_connector):
        _, mock_table = mock_connector

        result = repo.delete_by_key({"org_id": "o1", "id": "p1"})
        mock_table.delete_item.assert_called_once_with(Key={"org_id": "o1", "id": "p1"})
        assert result is True

    def test_list_all_no_filters(self, repo, mock_connector):
        _, mock_table = mock_connector
        mock_table.scan.return_value = {"Items": [{"id": "u1"}, {"id": "u2"}]}

        result = repo.list_all()
        assert len(result) == 2

    def test_list_all_with_pagination(self, repo, mock_connector):
        _, mock_table = mock_connector
        mock_table.scan.side_effect = [
            {"Items": [{"id": "u1"}], "LastEvaluatedKey": {"id": "u1"}},
            {"Items": [{"id": "u2"}]},
        ]

        result = repo.list_all()
        assert len(result) == 2
        assert mock_table.scan.call_count == 2

    def test_count_no_filters(self, repo, mock_connector):
        _, mock_table = mock_connector
        mock_table.scan.return_value = {"Count": 42}

        result = repo.count()
        assert result == 42

    def test_find_by(self, repo, mock_connector):
        _, mock_table = mock_connector
        mock_table.scan.return_value = {"Items": [{"id": "u1", "org_id": "o1"}]}

        result = repo.find_by("org_id", "o1")
        assert len(result) == 1


# ===========================================================================
# __getattr__ forwarding on entity wrappers
# ===========================================================================

class TestGetAttrForwarding:
    """Test that entity wrappers forward raw_* calls to underlying repo."""

    def test_user_repo_forwards_raw_get_item(self):
        mock_repo = MagicMock()
        mock_repo.raw_get_item.return_value = {"id": "u1"}

        user_repo = UserRepository(mock_repo)
        result = user_repo.raw_get_item({"id": "u1"})

        mock_repo.raw_get_item.assert_called_once_with({"id": "u1"})
        assert result == {"id": "u1"}

    def test_user_repo_forwards_raw_update_item(self):
        mock_repo = MagicMock()
        user_repo = UserRepository(mock_repo)

        user_repo.raw_update_item(Key={"id": "u1"}, UpdateExpression="SET #s = :v")
        mock_repo.raw_update_item.assert_called_once()

    def test_user_repo_forwards_raw_scan(self):
        mock_repo = MagicMock()
        mock_repo.raw_scan.return_value = {"Items": [], "Count": 0}

        user_repo = UserRepository(mock_repo)
        result = user_repo.raw_scan(Limit=1, Select="COUNT")

        mock_repo.raw_scan.assert_called_once_with(Limit=1, Select="COUNT")
        assert result["Count"] == 0

    def test_user_role_repo_forwards_raw_query(self):
        mock_repo = MagicMock()
        mock_repo.raw_query.return_value = {"Items": [], "Count": 0}

        ur_repo = UserRoleRepository(mock_repo)
        result = ur_repo.raw_query(IndexName="OrgMembersIndex")

        mock_repo.raw_query.assert_called_once()

    def test_getattr_raises_for_missing(self):
        mock_repo = MagicMock(spec=[])  # no attributes
        user_repo = UserRepository(mock_repo)

        with pytest.raises(AttributeError):
            user_repo.totally_nonexistent_method()


# ===========================================================================
# UserRepository specific methods
# ===========================================================================

class TestUserRepository:

    def test_find_by_email(self):
        mock_repo = MagicMock()
        mock_repo.find_by.return_value = [{"id": "u1", "email": "a@b.com"}]

        user_repo = UserRepository(mock_repo)
        result = user_repo.find_by_email("a@b.com")

        mock_repo.find_by.assert_called_once_with("email", "a@b.com")
        assert result["email"] == "a@b.com"

    def test_find_by_email_not_found(self):
        mock_repo = MagicMock()
        mock_repo.find_by.return_value = []

        user_repo = UserRepository(mock_repo)
        result = user_repo.find_by_email("missing@b.com")
        assert result is None

    def test_update_fields(self):
        mock_repo = MagicMock()
        mock_repo.update.return_value = {"id": "u1", "first_name": "Updated"}

        user_repo = UserRepository(mock_repo)
        result = user_repo.update_fields("u1", {"first_name": "Updated"})

        assert result is True
        call_args = mock_repo.update.call_args
        assert call_args[0][0] == "u1"
        assert "updated_at" in call_args[0][1]

    def test_scan_count(self):
        mock_repo = MagicMock()
        mock_repo.count.return_value = 42

        user_repo = UserRepository(mock_repo)
        assert user_repo.scan_count() == 42


# ===========================================================================
# ConfigRepository specific methods
# ===========================================================================

class TestConfigRepository:

    def test_put_and_get_settings(self):
        mock_repo = MagicMock()
        config_repo = ConfigRepository(mock_repo)

        config_repo.put_settings({"theme": "dark"})
        mock_repo.upsert.assert_called_once()
        call_item = mock_repo.upsert.call_args[0][0]
        assert call_item["pk"] == "APP"
        assert call_item["sk"] == "SETTINGS"

    def test_get_config_with_json_data(self):
        import json
        mock_repo = MagicMock()
        mock_repo.get_by_key.return_value = {
            "pk": "FEATURE", "sk": "flags",
            "data": json.dumps({"beta": True}),
        }

        config_repo = ConfigRepository(mock_repo)
        result = config_repo.get_config("FEATURE", "flags")

        assert result["beta"] is True

    def test_get_config_not_found(self):
        mock_repo = MagicMock()
        mock_repo.get_by_key.return_value = None

        config_repo = ConfigRepository(mock_repo)
        result = config_repo.get_config("MISSING", "key")
        assert result is None

    def test_scan_by_pk(self):
        import json
        mock_repo = MagicMock()
        mock_repo.find_by.return_value = [
            {"pk": "THEME", "sk": "dark", "data": json.dumps({"primary": "#000"})},
            {"pk": "THEME", "sk": "light", "data": json.dumps({"primary": "#fff"})},
        ]

        config_repo = ConfigRepository(mock_repo)
        result = config_repo.scan_by_pk("THEME")
        assert len(result) == 2


# ===========================================================================
# DatabaseService factory
# ===========================================================================

class TestDatabaseService:

    @patch.dict("os.environ", {"DB_TYPE": "dynamodb"}, clear=False)
    def test_dynamodb_init(self):
        with patch("database.repositories.connectors.DynamoDBConnector.DynamoDBConnector") as MockConn:
            mock_connector = MagicMock()
            mock_connector.get_repository.return_value = MagicMock()
            MockConn.return_value = mock_connector

            from services.database.DatabaseService import DatabaseService
            svc = DatabaseService()
            svc.initialize()

            mock_connector.initialize.assert_called_once()
            assert svc.users is not None
            assert svc.organizations is not None

    @patch.dict("os.environ", {"DB_TYPE": "invalid_db"}, clear=False)
    def test_invalid_db_type_raises(self):
        from services.database.DatabaseService import DatabaseService
        svc = DatabaseService()

        with pytest.raises(ValueError, match="Unsupported DB_TYPE"):
            svc.initialize()
