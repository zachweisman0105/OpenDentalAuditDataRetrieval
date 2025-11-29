"""Integration tests for credential configuration flow."""

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from opendental_cli.cli import main
from opendental_cli.credential_manager import get_credentials
from opendental_cli.models.credential import APICredential


class TestCredentialFlow:
    """Integration tests for credential setup and retrieval flow."""

    @patch("opendental_cli.cli.set_credentials")
    @patch("opendental_cli.cli.check_credentials_exist")
    def test_config_set_credentials_new(self, mock_check_exist, mock_set_credentials):
        """Test config set-credentials with new credentials."""
        mock_check_exist.return_value = False  # No existing credentials

        runner = CliRunner()
        result = runner.invoke(
            main,
            ["config", "set-credentials"],
            input="https://example.opendental.com/api/v1\ntest-dev-key-12345\ntest-cust-key-67890\n",
        )

        assert result.exit_code == 0
        assert "Credentials stored successfully" in result.output
        mock_set_credentials.assert_called_once_with(
            "https://example.opendental.com/api/v1",
            "test-dev-key-12345",
            "test-cust-key-67890",
            "production",
        )

    @patch("opendental_cli.cli.set_credentials")
    @patch("opendental_cli.cli.check_credentials_exist")
    def test_config_set_credentials_overwrite_confirmed(self, mock_check_exist, mock_set_credentials):
        """Test overwriting existing credentials when confirmed."""
        mock_check_exist.return_value = True  # Credentials exist

        runner = CliRunner()
        result = runner.invoke(
            main,
            ["config", "set-credentials"],
            input="y\nhttps://new.opendental.com/api/v1\nnew-dev-key\nnew-cust-key\n",
        )

        assert result.exit_code == 0
        assert "already configured" in result.output
        assert "Credentials stored successfully" in result.output
        mock_set_credentials.assert_called_once()

    @patch("opendental_cli.cli.check_credentials_exist")
    def test_config_set_credentials_overwrite_cancelled(self, mock_check_exist):
        """Test cancelling credential overwrite."""
        mock_check_exist.return_value = True

        runner = CliRunner()
        result = runner.invoke(
            main,
            ["config", "set-credentials"],
            input="n\n",  # Decline overwrite
        )

        assert result.exit_code == 0
        assert "Operation cancelled" in result.output

    @patch("opendental_cli.cli.set_credentials")
    @patch("opendental_cli.cli.check_credentials_exist")
    def test_config_set_credentials_staging_environment(self, mock_check_exist, mock_set_credentials):
        """Test setting credentials for staging environment."""
        mock_check_exist.return_value = False

        runner = CliRunner()
        result = runner.invoke(
            main,
            ["config", "set-credentials", "--environment", "staging"],
            input="https://staging.example.com/api/v1\nstaging-dev-key\nstaging-cust-key\n",
        )

        assert result.exit_code == 0
        mock_set_credentials.assert_called_once_with(
            "https://staging.example.com/api/v1",
            "staging-dev-key",
            "staging-cust-key",
            "staging",
        )

    @patch("opendental_cli.cli.check_credentials_exist")
    def test_config_set_credentials_invalid_url(self, mock_check_exist):
        """Test validation error for invalid URL."""
        mock_check_exist.return_value = False

        runner = CliRunner()
        result = runner.invoke(
            main,
            ["config", "set-credentials"],
            input="not-a-valid-url\ndev-key\ncust-key\n",
        )

        assert result.exit_code == 1
        assert "Invalid URL format" in result.output

    @patch("opendental_cli.cli.check_credentials_exist")
    def test_config_set_credentials_empty_developer_key(self, mock_check_exist):
        """Test error when developer key is empty."""
        mock_check_exist.return_value = False

        runner = CliRunner()
        result = runner.invoke(
            main,
            ["config", "set-credentials"],
            input="https://example.com/api/v1\n\n",  # Empty developer key
        )

        assert result.exit_code == 1
        assert "Developer Key cannot be empty" in result.output

    @patch("opendental_cli.cli.check_credentials_exist")
    def test_config_set_credentials_empty_customer_key(self, mock_check_exist):
        """Test error when customer key is empty."""
        mock_check_exist.return_value = False

        runner = CliRunner()
        result = runner.invoke(
            main,
            ["config", "set-credentials"],
            input="https://example.com/api/v1\ndev-key-123\n\n",  # Empty customer key
        )

        assert result.exit_code == 1
        assert "Customer Key cannot be empty" in result.output

    @patch("opendental_cli.credential_manager.keyring.get_password")
    @patch("opendental_cli.credential_manager.keyring.set_password")
    def test_full_credential_roundtrip(self, mock_set_password, mock_get_password):
        """Test full flow: set credentials, then retrieve them."""
        # Setup: credentials will be stored then retrieved
        stored_values = {}

        def set_side_effect(service, key, value):
            stored_values[f"{service}:{key}"] = value

        def get_side_effect(service, key):
            return stored_values.get(f"{service}:{key}")

        mock_set_password.side_effect = set_side_effect
        mock_get_password.side_effect = get_side_effect

        # Step 1: Set credentials via CLI
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["config", "set-credentials"],
            input="https://test.opendental.com/api/v1\ntest-dev-key\ntest-cust-key\n",
        )

        assert result.exit_code == 0
        assert "Credentials stored successfully" in result.output

        # Step 2: Retrieve credentials programmatically
        credentials = get_credentials()

        assert isinstance(credentials, APICredential)
        assert str(credentials.base_url) == "https://test.opendental.com/api/v1"
        assert credentials.developer_key.get_secret_value() == "test-dev-key"
        assert credentials.customer_key.get_secret_value() == "test-cust-key"
        assert credentials.environment == "production"

    @patch("opendental_cli.cli.get_credentials")
    def test_main_command_without_credentials(self, mock_get_credentials):
        """Test main command shows error when credentials not configured."""
        from opendental_cli.credential_manager import CredentialNotFoundError

        mock_get_credentials.side_effect = CredentialNotFoundError("No credentials")

        runner = CliRunner()
        result = runner.invoke(main, ["--patnum", "12345", "--aptnum", "67890"])

        assert result.exit_code == 1
        assert "No credentials" in result.output
        assert "config set-credentials" in result.output

    @patch("opendental_cli.cli.get_credentials")
    @patch("opendental_cli.cli.orchestrate_retrieval")
    def test_main_command_with_credentials(self, mock_orchestrate, mock_get_credentials):
        """Test main command proceeds when credentials exist."""
        mock_get_credentials.return_value = MagicMock(
            spec=APICredential,
            base_url="https://example.com/api/v1",
        )

        runner = CliRunner()
        result = runner.invoke(main, ["--patnum", "12345", "--aptnum", "67890"])

        # Should not fail on missing credentials
        assert "No credentials" not in result.output
        assert "config set-credentials" not in result.output or "TODO" in result.output
