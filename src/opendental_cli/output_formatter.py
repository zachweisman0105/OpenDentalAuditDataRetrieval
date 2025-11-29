"""Output Formatter for Audit Data.

Provides functions to write consolidated audit data to stdout or file
with proper formatting and permissions.

Article II Compliance: Encryption-at-Rest (file permissions 0o600)
"""

import json
import os
from pathlib import Path

from rich.console import Console
from rich.json import JSON

from opendental_cli.audit_logger import get_logger
from opendental_cli.models.response import ConsolidatedAuditData

logger = get_logger(__name__)
console = Console()


def write_to_stdout(data: ConsolidatedAuditData) -> None:
    """Write consolidated data to stdout with Rich formatting.

    Args:
        data: Consolidated audit data
    """
    json_str = data.model_dump_json(indent=2, exclude_none=True)
    console.print(JSON(json_str))
    logger.info("Output written to stdout")


def write_to_file(
    data: ConsolidatedAuditData,
    filepath: str,
    force: bool = False,
) -> None:
    """Write consolidated data to file with restrictive permissions.

    Creates output file with 0o600 permissions (owner read/write only)
    for HIPAA compliance. Prompts for confirmation if file exists
    unless force=True.

    Args:
        filepath: Output file path
        data: Consolidated audit data
        force: Skip overwrite confirmation

    Raises:
        FileExistsError: If file exists and user declines overwrite
        PermissionError: If insufficient write permissions
    """
    path = Path(filepath)

    # Check if file exists
    if path.exists() and not force:
        console.print(
            f"[yellow]File already exists: {filepath}[/yellow]",
            style="yellow",
        )
        response = console.input("Overwrite? [y/N]: ").strip().lower()
        if response not in ("y", "yes"):
            raise FileExistsError(f"File exists: {filepath}")

    # Ensure parent directory exists
    path.parent.mkdir(parents=True, exist_ok=True)

    # Write JSON to file
    json_str = data.model_dump_json(indent=2, exclude_none=True)

    try:
        # Write with restrictive permissions
        path.write_text(json_str, encoding="utf-8")

        # Set file permissions to 0o600 (owner read/write only)
        if os.name != "nt":  # Unix-like systems
            os.chmod(path, 0o600)
            logger.info(
                "Output written to file",
                filepath=str(path),
                permissions="0o600",
            )
        else:  # Windows
            # On Windows, use ACLs for equivalent protection
            import stat

            os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
            logger.info(
                "Output written to file",
                filepath=str(path),
                permissions="owner_only",
            )

        console.print(
            f"[green]✓ Output written to: {filepath}[/green]",
            style="green",
        )

    except PermissionError as e:
        logger.error(
            "Permission denied writing to file",
            filepath=str(path),
            error=str(e),
        )
        console.print(
            f"[red]✗ Permission denied: {filepath}[/red]",
            style="red",
        )
        raise e
