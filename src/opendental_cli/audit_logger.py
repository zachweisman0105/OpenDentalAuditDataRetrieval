"""Audit Logger Configuration.

Configures Structlog with PHI sanitization for HIPAA-compliant audit trails.
All logs use UTC timestamps and contain NO PHI data.

Article II Compliance: Audit Trail
"""

import os
import sys
from pathlib import Path

import structlog
from structlog.dev import ConsoleRenderer
from structlog.processors import (
    JSONRenderer,
    TimeStamper,
    add_log_level,
    format_exc_info,
)

from opendental_cli.phi_sanitizer import get_sanitizer


def configure_audit_logging(
    log_file: str | Path = "audit.log",
    log_level: str = "INFO",
) -> None:
    """Configure audit logging with PHI sanitization.

    Creates audit.log file with restrictive 0o600 permissions.
    Uses UTC timestamps and Structlog with PHI sanitizer.

    Args:
        log_file: Path to audit log file (default: audit.log)
        log_level: Logging level (default: INFO)

    Article II Compliance:
        - File permissions 0o600 (owner read/write only)
        - PHI sanitization processor
        - UTC timestamps
        - No PHI in log messages
    """
    log_path = Path(log_file)

    # Create log file with restrictive permissions if it doesn't exist
    if not log_path.exists():
        log_path.touch(mode=0o600)
    else:
        # Ensure existing file has correct permissions
        log_path.chmod(0o600)

    # Open log file for appending
    log_fp = log_path.open("a", encoding="utf-8")

    # Configure Structlog
    structlog.configure(
        processors=[
            add_log_level,  # Use structlog's add_log_level instead of stdlib version
            TimeStamper(fmt="iso", utc=True),  # UTC timestamps
            get_sanitizer(),  # PHI sanitization
            format_exc_info,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            JSONRenderer(),  # JSON format for parsing
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=log_fp),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = "opendental_cli") -> structlog.stdlib.BoundLogger:
    """Get a configured logger instance.

    Args:
        name: Logger name

    Returns:
        Configured Structlog bound logger
    """
    return structlog.get_logger(name)
