"""Credential Manager.

Manages OpenDental API credentials using OS keyring with environment variable fallback.
Keyring provides AES-256-GCM encryption on Windows, macOS, and Linux.

Article II Compliance: Credential Isolation, Encryption-at-Rest, Keyring Integration
"""

import os
import warnings
from typing import Optional

import keyring
from keyring.errors import KeyringError, NoKeyringError

from opendental_cli.models.credential import APICredential

# Service name for keyring storage
SERVICE_NAME = "opendental-audit-cli"


def set_credentials(
    base_url: str,
    developer_key: str,
    customer_key: str,
    environment: str = "production",
) -> None:
    """Store credentials in OS keyring.

    Args:
        base_url: OpenDental API base URL
        developer_key: Developer API key for authentication
        customer_key: Customer-specific API key for authentication
        environment: Environment name (production/staging/dev)

    Raises:
        NoKeyringError: If keyring backend is unavailable
    """
    try:
        # Store base_url
        keyring.set_password(SERVICE_NAME, f"{environment}_base_url", base_url)
        # Store developer_key
        keyring.set_password(SERVICE_NAME, f"{environment}_developer_key", developer_key)
        # Store customer_key
        keyring.set_password(SERVICE_NAME, f"{environment}_customer_key", customer_key)
        # Store environment marker
        keyring.set_password(SERVICE_NAME, "current_environment", environment)
    except NoKeyringError as e:
        raise NoKeyringError(
            "OS keyring is not available. "
            "Install gnome-keyring (Linux) or use environment variables as fallback."
        ) from e


def get_credentials(environment: Optional[str] = None) -> APICredential:
    """Retrieve credentials from keyring or environment variables.

    Priority:
        1. OS keyring (secure)
        2. Environment variables (fallback, with warning)

    Args:
        environment: Environment name (if None, uses stored current_environment)

    Returns:
        APICredential instance

    Raises:
        CredentialNotFoundError: If no credentials configured
    """
    # Try keyring first
    try:
        credentials = _get_from_keyring(environment)
        if credentials:
            return credentials
    except (KeyringError, NoKeyringError):
        pass  # Fall back to environment variables

    # Fallback to environment variables with warning
    warnings.warn(
        "Using environment variables for credentials. "
        "OS keyring is recommended for better security. "
        "Run 'opendental-cli config set-credentials' to use keyring.",
        UserWarning,
    )

    credentials = _get_from_env()
    if credentials:
        return credentials

    raise CredentialNotFoundError(
        "No credentials configured. "
        "Run 'opendental-cli config set-credentials' "
        "or set OPENDENTAL_BASE_URL, OPENDENTAL_DEVELOPER_KEY, and OPENDENTAL_CUSTOMER_KEY environment variables."
    )


def check_credentials_exist(environment: str = "production") -> bool:
    """Check if credentials exist in keyring or environment.

    Args:
        environment: Environment name

    Returns:
        True if credentials exist, False otherwise
    """
    # Check keyring first (without password verification)
    try:
        credentials = _get_from_keyring(environment)
        if credentials:
            return True
    except (KeyringError, NoKeyringError):
        pass
    
    # Check environment variables
    credentials = _get_from_env()
    return credentials is not None


def _get_from_keyring(environment: Optional[str]) -> Optional[APICredential]:
    """Get credentials from OS keyring.

    Args:
        environment: Environment name (if None, uses stored value)

    Returns:
        APICredential or None if not found
    """
    if environment is None:
        environment = keyring.get_password(SERVICE_NAME, "current_environment")
        if environment is None:
            return None

    base_url = keyring.get_password(SERVICE_NAME, f"{environment}_base_url")
    developer_key = keyring.get_password(SERVICE_NAME, f"{environment}_developer_key")
    customer_key = keyring.get_password(SERVICE_NAME, f"{environment}_customer_key")

    if base_url and developer_key and customer_key:
        return APICredential(
            base_url=base_url,
            developer_key=developer_key,
            customer_key=customer_key,
            environment=environment,
        )
    return None


def _get_from_env() -> Optional[APICredential]:
    """Get credentials from environment variables.

    Returns:
        APICredential or None if not found
    """
    base_url = os.getenv("OPENDENTAL_BASE_URL")
    developer_key = os.getenv("OPENDENTAL_DEVELOPER_KEY")
    customer_key = os.getenv("OPENDENTAL_CUSTOMER_KEY")
    environment = os.getenv("OPENDENTAL_ENVIRONMENT", "production")

    if base_url and developer_key and customer_key:
        return APICredential(
            base_url=base_url,
            developer_key=developer_key,
            customer_key=customer_key,
            environment=environment,
        )
    return None


class CredentialNotFoundError(Exception):
    """Raised when credentials are not configured."""

    pass
