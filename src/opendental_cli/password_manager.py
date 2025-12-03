"""Password Manager.

Manages master password for accessing OpenDental CLI credentials.
Uses bcrypt for password hashing and OS keyring for secure storage.

Article II Compliance: Credential Isolation, Encryption-at-Rest, Keyring Integration
"""

import keyring
from keyring.errors import KeyringError, NoKeyringError
import bcrypt
from typing import Optional

# Service name for password storage in keyring
PASSWORD_SERVICE_NAME = "opendental-audit-cli-password"
PASSWORD_USERNAME = "master_password_hash"


class PasswordError(Exception):
    """Base exception for password-related errors."""
    pass


class PasswordNotSetError(PasswordError):
    """Raised when password is not configured."""
    pass


class PasswordVerificationError(PasswordError):
    """Raised when password verification fails."""
    pass


def set_password(password: str) -> None:
    """Set master password for CLI access.
    
    Args:
        password: Master password to set (will be hashed with bcrypt)
        
    Raises:
        NoKeyringError: If keyring backend is unavailable
    """
    # Generate bcrypt hash with salt
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt(rounds=12)  # 12 rounds = good balance of security/performance
    password_hash = bcrypt.hashpw(password_bytes, salt)
    
    # Store hash in keyring
    try:
        keyring.set_password(
            PASSWORD_SERVICE_NAME,
            PASSWORD_USERNAME,
            password_hash.decode('utf-8')
        )
    except NoKeyringError as e:
        raise NoKeyringError(
            "OS keyring is not available. "
            "Install gnome-keyring (Linux) or ensure keyring service is running."
        ) from e


def verify_password(password: str) -> bool:
    """Verify password against stored hash.
    
    Args:
        password: Password to verify
        
    Returns:
        True if password matches, False otherwise
        
    Raises:
        PasswordNotSetError: If no password is configured
    """
    stored_hash = _get_password_hash()
    if stored_hash is None:
        raise PasswordNotSetError(
            "No master password configured. "
            "Run 'opendental-cli config set-password' to set password."
        )
    
    # Verify password using bcrypt
    password_bytes = password.encode('utf-8')
    stored_hash_bytes = stored_hash.encode('utf-8')
    
    try:
        return bcrypt.checkpw(password_bytes, stored_hash_bytes)
    except Exception:
        # If verification fails due to corrupted hash or other error
        return False


def check_password_exists() -> bool:
    """Check if master password is configured.
    
    Returns:
        True if password exists, False otherwise
    """
    return _get_password_hash() is not None


def change_password(old_password: str, new_password: str) -> None:
    """Change master password.
    
    Args:
        old_password: Current password for verification
        new_password: New password to set
        
    Raises:
        PasswordVerificationError: If old password is incorrect
        NoKeyringError: If keyring backend is unavailable
    """
    # Verify old password
    if not verify_password(old_password):
        raise PasswordVerificationError("Current password is incorrect")
    
    # Set new password
    set_password(new_password)


def delete_password() -> None:
    """Delete master password from keyring.
    
    WARNING: This will also prevent access to stored credentials.
    Credentials must be reconfigured after resetting password.
    """
    try:
        keyring.delete_password(PASSWORD_SERVICE_NAME, PASSWORD_USERNAME)
    except KeyringError:
        # Password doesn't exist or already deleted
        pass


def _get_password_hash() -> Optional[str]:
    """Get password hash from keyring.
    
    Returns:
        Password hash string or None if not found
    """
    try:
        return keyring.get_password(PASSWORD_SERVICE_NAME, PASSWORD_USERNAME)
    except (KeyringError, NoKeyringError):
        return None
