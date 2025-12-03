"""Unit tests for password_manager module.

Tests password hashing, verification, strength validation, and keyring storage.
"""

import pytest
from unittest.mock import patch, MagicMock
from keyring.errors import NoKeyringError

from opendental_cli.password_manager import (
    set_password,
    verify_password,
    check_password_exists,
    change_password,
    delete_password,
    PasswordError,
    PasswordNotSetError,
    PasswordVerificationError,
)


class TestPasswordHashing:
    """Test password hashing and storage."""
    
    @patch('opendental_cli.password_manager.keyring')
    def test_set_password_stores_hash_in_keyring(self, mock_keyring):
        """Test that set_password stores bcrypt hash in keyring."""
        # Arrange
        password = "MySecure123!"
        mock_keyring.set_password = MagicMock()
        
        # Act
        set_password(password)
        
        # Assert
        mock_keyring.set_password.assert_called_once()
        call_args = mock_keyring.set_password.call_args
        assert call_args[0][0] == "opendental-audit-cli-password"
        assert call_args[0][1] == "master_password_hash"
        # Verify stored value is a bcrypt hash (starts with $2b$)
        stored_hash = call_args[0][2]
        assert stored_hash.startswith("$2b$")
    
    @patch('opendental_cli.password_manager.keyring')
    def test_set_password_handles_no_keyring_error(self, mock_keyring):
        """Test that set_password raises NoKeyringError when keyring unavailable."""
        # Arrange
        password = "MySecure123!"
        mock_keyring.set_password.side_effect = NoKeyringError("Keyring not available")
        
        # Act & Assert
        with pytest.raises(NoKeyringError, match="keyring is not available"):
            set_password(password)


class TestPasswordVerification:
    """Test password verification."""
    
    @patch('opendental_cli.password_manager.keyring')
    def test_verify_password_success(self, mock_keyring):
        """Test that verify_password returns True for correct password."""
        # Arrange
        password = "MySecure123!"
        # Simulate actual bcrypt hash
        import bcrypt
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt(rounds=12)
        password_hash = bcrypt.hashpw(password_bytes, salt)
        
        mock_keyring.get_password.return_value = password_hash.decode('utf-8')
        
        # Act
        result = verify_password(password)
        
        # Assert
        assert result is True
    
    @patch('opendental_cli.password_manager.keyring')
    def test_verify_password_failure(self, mock_keyring):
        """Test that verify_password returns False for incorrect password."""
        # Arrange
        correct_password = "MySecure123!"
        wrong_password = "WrongPass456!"
        
        # Create hash of correct password
        import bcrypt
        password_bytes = correct_password.encode('utf-8')
        salt = bcrypt.gensalt(rounds=12)
        password_hash = bcrypt.hashpw(password_bytes, salt)
        
        mock_keyring.get_password.return_value = password_hash.decode('utf-8')
        
        # Act
        result = verify_password(wrong_password)
        
        # Assert
        assert result is False
    
    @patch('opendental_cli.password_manager.keyring')
    def test_verify_password_not_set(self, mock_keyring):
        """Test that verify_password raises PasswordNotSetError when no password configured."""
        # Arrange
        mock_keyring.get_password.return_value = None
        
        # Act & Assert
        with pytest.raises(PasswordNotSetError, match="No master password configured"):
            verify_password("AnyPassword123!")
    
    @patch('opendental_cli.password_manager.keyring')
    def test_verify_password_corrupted_hash(self, mock_keyring):
        """Test that verify_password handles corrupted hash gracefully."""
        # Arrange
        mock_keyring.get_password.return_value = "corrupted_hash_not_bcrypt"
        
        # Act
        result = verify_password("MySecure123!")
        
        # Assert
        assert result is False


class TestPasswordExists:
    """Test password existence checking."""
    
    @patch('opendental_cli.password_manager.keyring')
    def test_check_password_exists_true(self, mock_keyring):
        """Test check_password_exists returns True when password configured."""
        # Arrange
        mock_keyring.get_password.return_value = "$2b$12$somehash"
        
        # Act
        result = check_password_exists()
        
        # Assert
        assert result is True
    
    @patch('opendental_cli.password_manager.keyring')
    def test_check_password_exists_false(self, mock_keyring):
        """Test check_password_exists returns False when no password."""
        # Arrange
        mock_keyring.get_password.return_value = None
        
        # Act
        result = check_password_exists()
        
        # Assert
        assert result is False


class TestChangePassword:
    """Test password change functionality."""
    
    @patch('opendental_cli.password_manager.keyring')
    def test_change_password_success(self, mock_keyring):
        """Test that change_password updates password when old password correct."""
        # Arrange
        old_password = "OldSecure123!"
        new_password = "NewSecure456!"
        
        # Create hash of old password
        import bcrypt
        password_bytes = old_password.encode('utf-8')
        salt = bcrypt.gensalt(rounds=12)
        old_hash = bcrypt.hashpw(password_bytes, salt)
        
        mock_keyring.get_password.return_value = old_hash.decode('utf-8')
        mock_keyring.set_password = MagicMock()
        
        # Act
        change_password(old_password, new_password)
        
        # Assert
        mock_keyring.set_password.assert_called_once()
        # Verify new hash is stored
        call_args = mock_keyring.set_password.call_args
        new_hash = call_args[0][2]
        assert new_hash.startswith("$2b$")
        # Verify old and new hashes are different
        assert new_hash != old_hash.decode('utf-8')
    
    @patch('opendental_cli.password_manager.keyring')
    def test_change_password_wrong_old_password(self, mock_keyring):
        """Test that change_password raises error when old password incorrect."""
        # Arrange
        correct_old_password = "OldSecure123!"
        wrong_old_password = "WrongOld456!"
        new_password = "NewSecure789!"
        
        # Create hash of correct old password
        import bcrypt
        password_bytes = correct_old_password.encode('utf-8')
        salt = bcrypt.gensalt(rounds=12)
        old_hash = bcrypt.hashpw(password_bytes, salt)
        
        mock_keyring.get_password.return_value = old_hash.decode('utf-8')
        mock_keyring.set_password = MagicMock()
        
        # Act & Assert
        with pytest.raises(PasswordVerificationError, match="Current password is incorrect"):
            change_password(wrong_old_password, new_password)
        
        # Verify password was not updated
        mock_keyring.set_password.assert_not_called()


class TestDeletePassword:
    """Test password deletion."""
    
    @patch('opendental_cli.password_manager.keyring')
    def test_delete_password_success(self, mock_keyring):
        """Test that delete_password removes password from keyring."""
        # Arrange
        mock_keyring.delete_password = MagicMock()
        
        # Act
        delete_password()
        
        # Assert
        mock_keyring.delete_password.assert_called_once_with(
            "opendental-audit-cli-password",
            "master_password_hash"
        )
    
    @patch('opendental_cli.password_manager.keyring')
    def test_delete_password_not_found(self, mock_keyring):
        """Test that delete_password handles missing password gracefully."""
        # Arrange
        from keyring.errors import KeyringError
        mock_keyring.delete_password.side_effect = KeyringError("Not found")
        
        # Act - should not raise
        delete_password()
        
        # Assert
        mock_keyring.delete_password.assert_called_once()


class TestPasswordSaltUniqueness:
    """Test that password hashes use unique salts."""
    
    @patch('opendental_cli.password_manager.keyring')
    def test_same_password_different_hashes(self, mock_keyring):
        """Test that same password produces different hashes (due to unique salts)."""
        # Arrange
        password = "MySecure123!"
        stored_hashes = []
        
        def capture_hash(*args):
            stored_hashes.append(args[2])
        
        mock_keyring.set_password.side_effect = capture_hash
        
        # Act - set password twice
        set_password(password)
        set_password(password)
        
        # Assert - hashes should be different (different salts)
        assert len(stored_hashes) == 2
        assert stored_hashes[0] != stored_hashes[1]
        # But both should start with $2b$ (bcrypt identifier)
        assert stored_hashes[0].startswith("$2b$")
        assert stored_hashes[1].startswith("$2b$")
