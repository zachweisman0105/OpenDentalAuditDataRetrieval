"""Unit tests for output formatter.

Tests stdout and file output with proper permissions.
"""

import json
import os
import stat
from pathlib import Path
from unittest.mock import patch

import pytest

from opendental_cli.models.request import AuditDataRequest
from opendental_cli.models.response import ConsolidatedAuditData
from opendental_cli.output_formatter import write_to_file, write_to_stdout


@pytest.fixture
def sample_consolidated_data():
    """Create sample consolidated data."""
    request = AuditDataRequest(patnum=12345, aptnum=67890)
    return ConsolidatedAuditData(
        request=request,
        success={
            "patient": {"PatNum": 12345, "FName": "John", "LName": "Doe"},
            "appointment": {"AptNum": 67890, "PatNum": 12345},
        },
        failures=[
            {
                "endpoint": "billing",
                "http_status": "503",
                "error_message": "Service unavailable",
            }
        ],
        total_endpoints=6,
        successful_count=2,
        failed_count=1,
    )


def test_write_to_stdout(sample_consolidated_data, capsys):
    """Test writing to stdout."""
    write_to_stdout(sample_consolidated_data)

    captured = capsys.readouterr()
    # Rich adds color codes, so we just check for key content
    assert "12345" in captured.out
    assert "67890" in captured.out


def test_write_to_file_new_file(sample_consolidated_data, tmp_path):
    """Test writing to new file with 0o600 permissions."""
    output_file = tmp_path / "audit.json"

    write_to_file(sample_consolidated_data, str(output_file))

    # Verify file exists
    assert output_file.exists()

    # Verify content
    content = json.loads(output_file.read_text())
    assert content["request"]["patnum"] == 12345
    assert content["successful_count"] == 2
    assert content["failed_count"] == 1

    # Verify permissions (Unix-like systems only)
    if os.name != "nt":
        file_stat = output_file.stat()
        permissions = stat.S_IMODE(file_stat.st_mode)
        assert permissions == 0o600, f"Expected 0o600, got {oct(permissions)}"


def test_write_to_file_with_force_overwrite(sample_consolidated_data, tmp_path):
    """Test overwriting existing file with force=True."""
    output_file = tmp_path / "audit.json"
    output_file.write_text("old content")

    write_to_file(sample_consolidated_data, str(output_file), force=True)

    # Verify file was overwritten
    content = json.loads(output_file.read_text())
    assert content["request"]["patnum"] == 12345


@patch("opendental_cli.output_formatter.console.input")
def test_write_to_file_overwrite_confirmed(
    mock_input, sample_consolidated_data, tmp_path
):
    """Test overwriting existing file with user confirmation."""
    output_file = tmp_path / "audit.json"
    output_file.write_text("old content")

    # Simulate user confirming overwrite
    mock_input.return_value = "y"

    write_to_file(sample_consolidated_data, str(output_file), force=False)

    # Verify file was overwritten
    content = json.loads(output_file.read_text())
    assert content["request"]["patnum"] == 12345


@patch("opendental_cli.output_formatter.console.input")
def test_write_to_file_overwrite_cancelled(
    mock_input, sample_consolidated_data, tmp_path
):
    """Test cancelling overwrite of existing file."""
    output_file = tmp_path / "audit.json"
    output_file.write_text("old content")

    # Simulate user declining overwrite
    mock_input.return_value = "n"

    with pytest.raises(FileExistsError):
        write_to_file(sample_consolidated_data, str(output_file), force=False)

    # Verify file was not overwritten
    assert output_file.read_text() == "old content"


def test_write_to_file_creates_parent_directory(sample_consolidated_data, tmp_path):
    """Test that parent directories are created if missing."""
    output_file = tmp_path / "nested" / "dir" / "audit.json"

    write_to_file(sample_consolidated_data, str(output_file))

    assert output_file.exists()
    content = json.loads(output_file.read_text())
    assert content["request"]["patnum"] == 12345


def test_write_to_file_permission_error(sample_consolidated_data, tmp_path):
    """Test handling of permission errors."""
    # Create read-only directory
    readonly_dir = tmp_path / "readonly"
    readonly_dir.mkdir()

    if os.name != "nt":
        # Make directory read-only on Unix
        os.chmod(readonly_dir, 0o444)

        output_file = readonly_dir / "audit.json"

        with pytest.raises(PermissionError):
            write_to_file(sample_consolidated_data, str(output_file))

        # Cleanup: restore permissions
        os.chmod(readonly_dir, 0o755)
