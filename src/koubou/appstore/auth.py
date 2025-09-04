"""App Store Connect authentication using JWT tokens."""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from time import mktime, time
from typing import Dict

import jwt
from cryptography.hazmat.primitives.serialization import load_pem_private_key

from ..exceptions import KoubouError

logger = logging.getLogger(__name__)


class AppStoreAuthError(KoubouError):
    """Error related to App Store Connect authentication."""

    pass


class AppStoreCredentials:
    """App Store Connect API credentials."""

    def __init__(self, key_id: str, issuer_id: str, private_key_path: str, app_id: str):
        """Initialize credentials.

        Args:
            key_id: API key ID from App Store Connect
            issuer_id: Issuer ID from App Store Connect
            private_key_path: Path to .p8 private key file
            app_id: App Store Connect app ID
        """
        self.key_id = key_id
        self.issuer_id = issuer_id
        self.private_key_path = Path(private_key_path).expanduser()
        self.app_id = app_id

        # Validate private key file exists
        if not self.private_key_path.exists():
            raise AppStoreAuthError(
                f"Private key file not found: {self.private_key_path}"
            )

    @classmethod
    def from_config_file(cls, config_path: Path) -> "AppStoreCredentials":
        """Load credentials from JSON config file.

        Args:
            config_path: Path to appstore-config.json file

        Returns:
            AppStoreCredentials instance

        Raises:
            AppStoreAuthError: If config file is invalid or missing required fields
        """
        if not config_path.exists():
            raise AppStoreAuthError(f"Config file not found: {config_path}")

        try:
            with open(config_path) as f:
                config_data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            raise AppStoreAuthError(f"Failed to read config file: {e}") from e

        # Validate required fields
        required_fields = ["key_id", "issuer_id", "private_key_path", "app_id"]
        missing_fields = [
            field for field in required_fields if field not in config_data
        ]

        if missing_fields:
            raise AppStoreAuthError(
                f"Missing required fields in config: {', '.join(missing_fields)}"
            )

        # Resolve private key path relative to config file directory if not absolute
        private_key_path = Path(config_data["private_key_path"])
        if not private_key_path.is_absolute():
            private_key_path = config_path.parent / private_key_path

        return cls(
            key_id=config_data["key_id"],
            issuer_id=config_data["issuer_id"],
            private_key_path=str(private_key_path),
            app_id=config_data["app_id"],
        )


class AppStoreAuth:
    """Handles App Store Connect authentication with JWT tokens."""

    def __init__(self, credentials: AppStoreCredentials):
        """Initialize authenticator.

        Args:
            credentials: App Store Connect credentials
        """
        self.credentials = credentials
        self._private_key = None
        self._current_token = None
        self._token_expires_at = None

    def _load_private_key(self) -> bytes:
        """Load and cache the private key."""
        if self._private_key is None:
            try:
                with open(self.credentials.private_key_path, "rb") as f:
                    key_data = f.read()

                # Validate that we can load the key
                load_pem_private_key(key_data, password=None)
                self._private_key = key_data

            except Exception as e:
                raise AppStoreAuthError(
                    f"Failed to load private key from "
                    f"{self.credentials.private_key_path}: {e}"
                ) from e

        return self._private_key

    def generate_token(self) -> str:
        """Generate a new JWT token for App Store Connect API.

        Returns:
            JWT token string

        Raises:
            AppStoreAuthError: If token generation fails
        """
        try:
            # Token expires in 19 minutes (under the 20-minute limit)
            expiration_time = datetime.now() + timedelta(minutes=19)

            headers = {"alg": "ES256", "kid": self.credentials.key_id, "typ": "JWT"}

            payload = {
                "iss": self.credentials.issuer_id,
                "iat": int(time()),
                "exp": int(mktime(expiration_time.timetuple())),
                "aud": "appstoreconnect-v1",
            }

            private_key = self._load_private_key()

            token = jwt.encode(payload, private_key, algorithm="ES256", headers=headers)

            # Update cache
            self._current_token = token
            self._token_expires_at = expiration_time

            logger.debug("Generated new JWT token")
            return token

        except Exception as e:
            raise AppStoreAuthError(f"Failed to generate JWT token: {e}") from e

    def get_valid_token(self) -> str:
        """Get a valid JWT token, generating a new one if needed.

        Returns:
            Valid JWT token string
        """
        # Check if we need a new token (expired or doesn't exist)
        if (
            self._current_token is None
            or self._token_expires_at is None
            or datetime.now() >= self._token_expires_at - timedelta(minutes=1)
        ):  # Refresh 1 min early

            logger.debug("Generating new token (expired or missing)")
            return self.generate_token()

        logger.debug("Using cached token")
        return self._current_token

    def get_auth_headers(self) -> Dict[str, str]:
        """Get HTTP headers for authenticated requests.

        Returns:
            Dictionary with Authorization header
        """
        token = self.get_valid_token()
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    def validate_credentials(self) -> bool:
        """Validate that credentials work by generating a test token.

        Returns:
            True if credentials are valid

        Raises:
            AppStoreAuthError: If credentials are invalid
        """
        try:
            self.generate_token()
            logger.info("Credentials validated successfully")
            return True
        except Exception as e:
            raise AppStoreAuthError(f"Credential validation failed: {e}") from e


def create_config_file(config_path: Path, credentials_data: Dict[str, str]) -> None:
    """Create an App Store Connect config file.

    Args:
        config_path: Path where to create the config file
        credentials_data: Dictionary with credentials (key_id, issuer_id, etc.)

    Raises:
        AppStoreAuthError: If config creation fails
    """
    try:
        # Ensure directory exists
        config_path.parent.mkdir(parents=True, exist_ok=True)

        # Create config with proper formatting
        config_content = {
            "key_id": credentials_data["key_id"],
            "issuer_id": credentials_data["issuer_id"],
            "private_key_path": credentials_data["private_key_path"],
            "app_id": credentials_data["app_id"],
        }

        with open(config_path, "w") as f:
            json.dump(config_content, f, indent=2)

        # Set restrictive permissions (readable only by owner)
        config_path.chmod(0o600)

        logger.info(f"Created App Store Connect config: {config_path}")

    except Exception as e:
        raise AppStoreAuthError(f"Failed to create config file: {e}") from e
