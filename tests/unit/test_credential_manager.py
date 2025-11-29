"""Unit tests for credential_manager module."""

import os
from unittest.mock import MagicMock, patch

import pytest
from keyring.errors import NoKeyringError

from opendental_cli.credential_manager import (
    CredentialNotFoundError,
    check_credentials_exist,
    get_credentials,
    set_credentials,
)
from opendental_cli.models.credential import APICredential


class TestSetCredentials:
    """Tests for set_credentials function."""

    @patch("opendental_cli.credential_manager.keyring.set_password")
    def test_set_credentials_stores_in_keyring(self, mock_set_password):
        """Test credentials are stored in keyring."""
        base_url = "https://example.opendental.com/api/v1"
        developer_key = "test-developer-key-12345"
        customer_key = "test-customer-key-12345"
        environment = "production"

        set_credentials(base_url, developer_key, customer_key, environment)

        # Verify keyring.set_password called for base_url, developer_key, customer_key, and environment
        assert mock_set_password.call_count == 4
        calls = mock_set_password.call_args_list

        # Check base_url stored
        assert calls[0][0] == ("opendental-audit-cli", "production_base_url", base_url)
        # Check developer_key stored
        assert calls[1][0] == ("opendental-audit-cli", "production_developer_key", developer_key)
        # Check customer_key stored
        assert calls[2][0] == ("opendental-audit-cli", "production_customer_key", customer_key)
        # Check environment marker stored
        assert calls[3][0] == ("opendental-audit-cli", "current_environment", environment)

    @patch("opendental_cli.credential_manager.keyring.set_password")
    def test_set_credentials_staging_environment(self, mock_set_password):
        """Test credentials stored with staging environment."""
        base_url = "https://staging.opendental.com/api/v1"
        developer_key = "staging-developer-key"
        customer_key = "staging-customer-key"
        environment = "staging"

        set_credentials(base_url, developer_key, customer_key, environment)

        calls = mock_set_password.call_args_list
        assert calls[0][0] == ("opendental-audit-cli", "staging_base_url", base_url)
        assert calls[1][0] == ("opendental-audit-cli", "staging_developer_key", developer_key)
        assert calls[2][0] == ("opendental-audit-cli", "staging_customer_key", customer_key)

    @patch("opendental_cli.credential_manager.keyring.set_password")
    def test_set_credentials_raises_on_no_keyring(self, mock_set_password):
        """Test NoKeyringError raised when keyring unavailable."""
        mock_set_password.side_effect = NoKeyringError("No keyring backend found")

        with pytest.raises(NoKeyringError) as exc_info:
            set_credentials("https://example.com/api", "key", "production")

        assert "OS keyring is not available" in str(exc_info.value)


class TestGetCredentials:
    """Tests for get_credentials function."""

    @patch("opendental_cli.credential_manager.keyring.get_password")
    def test_get_credentials_from_keyring(self, mock_get_password):
        """Test credentials retrieved from keyring."""
        mock_get_password.side_effect = [
            "production",  # current_environment
            "https://example.opendental.com/api/v1",  # base_url
            "test-developer-key",  # developer_key
            "test-customer-key",  # customer_key
        ]

        credentials = get_credentials()

        assert isinstance(credentials, APICredential)
        assert str(credentials.base_url) == "https://example.opendental.com/api/v1"
        assert credentials.developer_key.get_secret_value() == "test-developer-key"
        assert credentials.customer_key.get_secret_value() == "test-customer-key"
        assert credentials.environment == "production"

    @patch("opendental_cli.credential_manager.keyring.get_password")
    def test_get_credentials_with_explicit_environment(self, mock_get_password):
        """Test credentials retrieved for specific environment."""
        mock_get_password.side_effect = [
            "https://staging.opendental.com/api/v1",  # staging_base_url
            "staging-developer-key",  # staging_developer_key
            "staging-customer-key",  # staging_customer_key
        ]

        credentials = get_credentials(environment="staging")

        assert str(credentials.base_url) == "https://staging.opendental.com/api/v1"
        assert credentials.developer_key.get_secret_value() == "staging-developer-key"
        assert credentials.customer_key.get_secret_value() == "staging-customer-key"
        assert credentials.environment == "staging"

    @patch("opendental_cli.credential_manager.keyring.get_password")
    def test_get_credentials_fallback_to_env_vars(self, mock_get_password):
        """Test fallback to environment variables when keyring unavailable."""
        mock_get_password.return_value = None  # Keyring returns None

        with patch.dict(
            os.environ,
            {
                "OPENDENTAL_BASE_URL": "https://env.opendental.com/api/v1",
                "OPENDENTAL_DEVELOPER_KEY": "env-developer-key",
                "OPENDENTAL_CUSTOMER_KEY": "env-customer-key",
                "OPENDENTAL_ENVIRONMENT": "dev",
            },
        ):
            with pytest.warns(UserWarning, match="Using environment variables"):
                credentials = get_credentials()

            assert str(credentials.base_url) == "https://env.opendental.com/api/v1"
            assert credentials.developer_key.get_secret_value() == "env-developer-key"
            assert credentials.customer_key.get_secret_value() == "env-customer-key"
            assert credentials.environment == "dev"

    @patch("opendental_cli.credential_manager.keyring.get_password")
    def test_get_credentials_env_vars_default_environment(self, mock_get_password):
        """Test environment defaults to production from env vars."""
        mock_get_password.return_value = None

        with patch.dict(
            os.environ,
            {
                "OPENDENTAL_BASE_URL": "https://example.com/api/v1",
                "OPENDENTAL_DEVELOPER_KEY": "developer-key",
                "OPENDENTAL_CUSTOMER_KEY": "customer-key",
            },
            clear=True,
        ):
            with pytest.warns(UserWarning):
                credentials = get_credentials()

            assert credentials.environment == "production"

    @patch("opendental_cli.credential_manager.keyring.get_password")
    def test_get_credentials_raises_when_not_found(self, mock_get_password):
        """Test CredentialNotFoundError when no credentials available."""
        mock_get_password.return_value = None

        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(CredentialNotFoundError) as exc_info:
                get_credentials()

            assert "No credentials configured" in str(exc_info.value)
            assert "config set-credentials" in str(exc_info.value)


class TestCheckCredentialsExist:
    """Tests for check_credentials_exist function."""

    @patch("opendental_cli.credential_manager.get_credentials")
    def test_returns_true_when_credentials_exist(self, mock_get_credentials):
        """Test returns True when credentials found."""
        mock_get_credentials.return_value = MagicMock(spec=APICredential)

        result = check_credentials_exist("production")

        assert result is True

    @patch("opendental_cli.credential_manager.get_credentials")
    def test_returns_false_when_credentials_not_found(self, mock_get_credentials):
        """Test returns False when credentials not found."""
        mock_get_credentials.side_effect = CredentialNotFoundError("Not found")

        result = check_credentials_exist("production")

        assert result is False
