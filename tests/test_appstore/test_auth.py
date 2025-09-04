"""Tests for App Store Connect authentication."""

import json
from datetime import datetime, timedelta
from unittest.mock import mock_open, patch

import pytest

from koubou.appstore.auth import (
    AppStoreAuth,
    AppStoreAuthError,
    AppStoreCredentials,
    create_config_file,
)


class TestAppStoreCredentials:
    """Test AppStoreCredentials class."""

    def test_init_with_valid_data(self, tmp_path):
        """Test initialization with valid credential data."""
        # Create a temporary private key file
        key_file = tmp_path / "test_key.p8"
        key_file.write_text(
            "-----BEGIN PRIVATE KEY-----\ntest_key_content\n-----END PRIVATE KEY-----"  # DUMMY KEY
        )

        credentials = AppStoreCredentials(
            key_id="ABC123",
            issuer_id="12345678-1234-1234-1234-123456789012",
            private_key_path=str(key_file),
            app_id="987654321",
        )

        assert credentials.key_id == "ABC123"
        assert credentials.issuer_id == "12345678-1234-1234-1234-123456789012"
        assert credentials.private_key_path == key_file
        assert credentials.app_id == "987654321"

    def test_init_with_missing_key_file(self):
        """Test initialization with missing private key file."""
        with pytest.raises(AppStoreAuthError, match="Private key file not found"):
            AppStoreCredentials(
                key_id="ABC123",
                issuer_id="12345678-1234-1234-1234-123456789012",
                private_key_path="/nonexistent/key.p8",
                app_id="987654321",
            )

    def test_from_config_file_valid(self, tmp_path):
        """Test loading credentials from valid config file."""
        # Create temporary private key file
        key_file = tmp_path / "AuthKey_ABC123.p8"
        key_file.write_text(
            "-----BEGIN PRIVATE KEY-----\ntest_content\n-----END PRIVATE KEY-----"  # DUMMY KEY
        )

        # Create config file
        config_file = tmp_path / "appstore-config.json"
        config_data = {
            "key_id": "ABC123",
            "issuer_id": "12345678-1234-1234-1234-123456789012",
            "private_key_path": "AuthKey_ABC123.p8",  # Relative path
            "app_id": "987654321",
        }

        with open(config_file, "w") as f:
            json.dump(config_data, f)

        credentials = AppStoreCredentials.from_config_file(config_file)

        assert credentials.key_id == "ABC123"
        assert credentials.issuer_id == "12345678-1234-1234-1234-123456789012"
        assert (
            credentials.private_key_path == key_file
        )  # Should resolve to absolute path
        assert credentials.app_id == "987654321"

    def test_from_config_file_missing_file(self, tmp_path):
        """Test loading from nonexistent config file."""
        config_file = tmp_path / "nonexistent.json"

        with pytest.raises(AppStoreAuthError, match="Config file not found"):
            AppStoreCredentials.from_config_file(config_file)

    def test_from_config_file_invalid_json(self, tmp_path):
        """Test loading from invalid JSON file."""
        config_file = tmp_path / "invalid.json"
        config_file.write_text("{ invalid json")

        with pytest.raises(AppStoreAuthError, match="Failed to read config file"):
            AppStoreCredentials.from_config_file(config_file)

    def test_from_config_file_missing_fields(self, tmp_path):
        """Test loading from config file with missing required fields."""
        config_file = tmp_path / "incomplete.json"
        config_data = {
            "key_id": "ABC123",
            # Missing issuer_id, private_key_path, app_id
        }

        with open(config_file, "w") as f:
            json.dump(config_data, f)

        with pytest.raises(AppStoreAuthError, match="Missing required fields"):
            AppStoreCredentials.from_config_file(config_file)


class TestAppStoreAuth:
    """Test AppStoreAuth class."""

    @pytest.fixture
    def mock_credentials(self, tmp_path):
        """Create mock credentials for testing."""
        key_file = tmp_path / "test_key.p8"
        # Create a simple test private key (DUMMY KEY - NOT A REAL SECRET)
        # This won't be used for actual signing in tests
        key_content = """-----BEGIN PRIVATE KEY-----
MIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQg7S8j1SWx8KGjTZsW
Tkj3mD7VUE6ZXj+KbhX4d/UgG2ihRANCAASH9j8YHdJ+Y7z8YlYrHK9TsL7fF1S4
F8MJTcLQaR8Y3fH8dP4jX2+8uEH5qJg8yR2c0pKQ7f4nK8KjW1n1s2
-----END PRIVATE KEY-----"""
        key_file.write_text(key_content)

        return AppStoreCredentials(
            key_id="ABC123",
            issuer_id="12345678-1234-1234-1234-123456789012",
            private_key_path=str(key_file),
            app_id="987654321",
        )

    def test_init(self, mock_credentials):
        """Test initialization of AppStoreAuth."""
        auth = AppStoreAuth(mock_credentials)

        assert auth.credentials == mock_credentials
        assert auth._private_key is None
        assert auth._current_token is None
        assert auth._token_expires_at is None

    @patch("koubou.appstore.auth.load_pem_private_key")
    def test_load_private_key(self, mock_load_key, mock_credentials):
        """Test private key loading."""
        auth = AppStoreAuth(mock_credentials)

        # Mock successful key loading
        mock_load_key.return_value = "mock_key_object"

        with patch("builtins.open", mock_open(read_data=b"test_key_data")):
            result = auth._load_private_key()

        assert result == b"test_key_data"
        assert auth._private_key == b"test_key_data"
        mock_load_key.assert_called_once_with(b"test_key_data", password=None)

    @patch("koubou.appstore.auth.jwt.encode")
    @patch("koubou.appstore.auth.AppStoreAuth._load_private_key")
    def test_generate_token(self, mock_load_key, mock_jwt_encode, mock_credentials):
        """Test JWT token generation."""
        auth = AppStoreAuth(mock_credentials)

        # Mock dependencies
        mock_load_key.return_value = b"test_private_key"
        mock_jwt_encode.return_value = "test_jwt_token"

        with patch("koubou.appstore.auth.time") as mock_time:
            mock_time.return_value = 1640995200.0  # Fixed timestamp

            token = auth.generate_token()

        assert token == "test_jwt_token"
        assert auth._current_token == "test_jwt_token"
        assert auth._token_expires_at is not None

        # Verify JWT encode was called with correct parameters
        mock_jwt_encode.assert_called_once()
        call_args = mock_jwt_encode.call_args

        # Check payload
        payload = call_args[0][0]
        assert payload["iss"] == "12345678-1234-1234-1234-123456789012"
        assert payload["aud"] == "appstoreconnect-v1"
        assert "iat" in payload
        assert "exp" in payload

        # Check headers
        headers = call_args[1]["headers"]
        assert headers["alg"] == "ES256"
        assert headers["kid"] == "ABC123"
        assert headers["typ"] == "JWT"

    @patch("koubou.appstore.auth.AppStoreAuth.generate_token")
    def test_get_valid_token_no_existing_token(self, mock_generate, mock_credentials):
        """Test getting valid token when none exists."""
        auth = AppStoreAuth(mock_credentials)
        mock_generate.return_value = "new_token"

        token = auth.get_valid_token()

        assert token == "new_token"
        mock_generate.assert_called_once()

    @patch("koubou.appstore.auth.AppStoreAuth.generate_token")
    def test_get_valid_token_expired_token(self, mock_generate, mock_credentials):
        """Test getting valid token when existing token is expired."""
        auth = AppStoreAuth(mock_credentials)

        # Set up expired token
        auth._current_token = "expired_token"
        auth._token_expires_at = datetime.now() - timedelta(minutes=1)
        mock_generate.return_value = "new_token"

        token = auth.get_valid_token()

        assert token == "new_token"
        mock_generate.assert_called_once()

    def test_get_valid_token_valid_existing_token(self, mock_credentials):
        """Test getting valid token when existing token is still valid."""
        auth = AppStoreAuth(mock_credentials)

        # Set up valid token
        auth._current_token = "valid_token"
        auth._token_expires_at = datetime.now() + timedelta(minutes=10)

        with patch("koubou.appstore.auth.AppStoreAuth.generate_token") as mock_generate:
            token = auth.get_valid_token()

        assert token == "valid_token"
        mock_generate.assert_not_called()

    @patch("koubou.appstore.auth.AppStoreAuth.get_valid_token")
    def test_get_auth_headers(self, mock_get_token, mock_credentials):
        """Test getting authentication headers."""
        auth = AppStoreAuth(mock_credentials)
        mock_get_token.return_value = "test_token"

        headers = auth.get_auth_headers()

        expected_headers = {
            "Authorization": "Bearer test_token",
            "Content-Type": "application/json",
        }

        assert headers == expected_headers
        mock_get_token.assert_called_once()

    @patch("koubou.appstore.auth.AppStoreAuth.generate_token")
    def test_validate_credentials_success(self, mock_generate, mock_credentials):
        """Test successful credential validation."""
        auth = AppStoreAuth(mock_credentials)
        mock_generate.return_value = "test_token"

        result = auth.validate_credentials()

        assert result is True
        mock_generate.assert_called_once()

    @patch("koubou.appstore.auth.AppStoreAuth.generate_token")
    def test_validate_credentials_failure(self, mock_generate, mock_credentials):
        """Test credential validation failure."""
        auth = AppStoreAuth(mock_credentials)
        mock_generate.side_effect = Exception("Token generation failed")

        with pytest.raises(AppStoreAuthError, match="Credential validation failed"):
            auth.validate_credentials()


class TestCreateConfigFile:
    """Test create_config_file function."""

    def test_create_config_file_success(self, tmp_path):
        """Test successful config file creation."""
        config_path = tmp_path / "test-config.json"
        credentials_data = {
            "key_id": "ABC123",
            "issuer_id": "12345678-1234-1234-1234-123456789012",
            "private_key_path": "./AuthKey_ABC123.p8",
            "app_id": "987654321",
        }

        create_config_file(config_path, credentials_data)

        # Verify file was created
        assert config_path.exists()

        # Verify file permissions (should be 600 - owner read/write only)
        assert oct(config_path.stat().st_mode)[-3:] == "600"

        # Verify file contents
        with open(config_path) as f:
            saved_data = json.load(f)

        assert saved_data == credentials_data

    def test_create_config_file_creates_directory(self, tmp_path):
        """Test config file creation creates parent directories."""
        config_path = tmp_path / "subdir" / "test-config.json"
        credentials_data = {
            "key_id": "ABC123",
            "issuer_id": "12345678-1234-1234-1234-123456789012",
            "private_key_path": "./AuthKey_ABC123.p8",
            "app_id": "987654321",
        }

        create_config_file(config_path, credentials_data)

        # Verify directory and file were created
        assert config_path.parent.exists()
        assert config_path.exists()

    def test_create_config_file_handles_errors(self, tmp_path):
        """Test config file creation handles errors gracefully."""
        # Try to create file in read-only directory (will fail)
        readonly_dir = tmp_path / "readonly"
        readonly_dir.mkdir()
        readonly_dir.chmod(0o444)  # Read-only

        config_path = readonly_dir / "test-config.json"
        credentials_data = {
            "key_id": "ABC123",
            "issuer_id": "12345678-1234-1234-1234-123456789012",
            "private_key_path": "./AuthKey_ABC123.p8",
            "app_id": "987654321",
        }

        with pytest.raises(AppStoreAuthError, match="Failed to create config file"):
            create_config_file(config_path, credentials_data)
