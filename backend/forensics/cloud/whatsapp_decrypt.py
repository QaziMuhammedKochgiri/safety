"""
WhatsApp Backup Decryption Module

Supports crypt14 and crypt15 encrypted backup formats.
Uses wa-crypt-tools library for decryption.

crypt14: Requires 64-byte key file (typically from /data/data/com.whatsapp/files/key)
crypt15: Requires 158-byte encrypted key file + Google account data

For legal/ethical use only in authorized forensic investigations.
"""

import os
import struct
import hashlib
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class DecryptionResult:
    """Result of a decryption attempt."""
    success: bool
    output_path: Optional[str] = None
    error: Optional[str] = None
    format_version: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class WhatsAppKeyExtractor:
    """
    Extract and manage WhatsApp encryption keys.

    Key sources:
    - crypt14: /data/data/com.whatsapp/files/key (64 bytes)
    - crypt15: /data/data/com.whatsapp/files/encrypted_backup.key (158 bytes)

    Note: Key extraction requires root access or ADB backup on Android device.
    """

    CRYPT14_KEY_SIZE = 64
    CRYPT15_KEY_SIZE = 158

    def __init__(self, key_path: Optional[str] = None):
        """Initialize key extractor with optional key file path."""
        self.key_path = key_path
        self._key_data = None
        self._key_type = None

    def load_key_file(self, path: str) -> Tuple[bool, str]:
        """
        Load encryption key from file.

        Args:
            path: Path to key file

        Returns:
            Tuple of (success, message/key_type)
        """
        try:
            with open(path, 'rb') as f:
                self._key_data = f.read()

            key_size = len(self._key_data)

            if key_size == self.CRYPT14_KEY_SIZE:
                self._key_type = 'crypt14'
                return True, 'crypt14'
            elif key_size == self.CRYPT15_KEY_SIZE:
                self._key_type = 'crypt15'
                return True, 'crypt15'
            else:
                return False, f'Unknown key size: {key_size} bytes'

        except FileNotFoundError:
            return False, f'Key file not found: {path}'
        except Exception as e:
            return False, f'Error reading key file: {str(e)}'

    def extract_from_adb_backup(self, backup_path: str, output_dir: str) -> Tuple[bool, str]:
        """
        Extract key from ADB backup file.

        ADB backup structure (ab file):
        - Header: "ANDROID BACKUP" + version + flags
        - Compressed tar with app data

        Args:
            backup_path: Path to .ab ADB backup file
            output_dir: Directory to extract to

        Returns:
            Tuple of (success, key_path or error)
        """
        try:
            import tarfile
            import zlib

            with open(backup_path, 'rb') as f:
                # Skip header (usually 24 bytes)
                header = f.readline()  # ANDROID BACKUP
                version = f.readline()
                compressed = f.readline()
                encryption = f.readline()

                # Read rest as potentially compressed data
                data = f.read()

            # Try to decompress
            try:
                decompressed = zlib.decompress(data)
            except zlib.error:
                decompressed = data  # Might not be compressed

            # Write to temp tar
            tar_path = Path(output_dir) / 'backup.tar'
            with open(tar_path, 'wb') as f:
                f.write(decompressed)

            # Extract from tar
            with tarfile.open(tar_path, 'r') as tar:
                # Look for key files
                for member in tar.getmembers():
                    if 'key' in member.name.lower() and 'whatsapp' in member.name.lower():
                        tar.extract(member, output_dir)
                        key_path = Path(output_dir) / member.name
                        success, msg = self.load_key_file(str(key_path))
                        if success:
                            return True, str(key_path)

            return False, 'No WhatsApp key found in backup'

        except Exception as e:
            return False, f'ADB extraction failed: {str(e)}'

    @property
    def key_data(self) -> Optional[bytes]:
        """Get loaded key data."""
        return self._key_data

    @property
    def key_type(self) -> Optional[str]:
        """Get detected key type."""
        return self._key_type


class WhatsAppBackupDecryptor:
    """
    Decrypt WhatsApp backup files (msgstore.db.crypt14/crypt15).

    Supported formats:
    - crypt14: AES-256-GCM with 64-byte key
    - crypt15: AES-256-GCM with encrypted key (requires Google account)

    Usage:
        decryptor = WhatsAppBackupDecryptor()
        decryptor.load_key('/path/to/key')
        result = decryptor.decrypt('/path/to/msgstore.db.crypt14', '/output/dir')
    """

    # crypt14 header constants
    CRYPT14_HEADER_SIZE = 67
    CRYPT14_KEY_OFFSET = 3  # Skip first 3 bytes
    CRYPT14_IV_OFFSET = 51  # IV location in header
    CRYPT14_IV_SIZE = 16

    # crypt15 header constants
    CRYPT15_HEADER_SIZE = 99

    def __init__(self):
        """Initialize decryptor."""
        self.key_extractor = WhatsAppKeyExtractor()
        self._wa_crypt_available = self._check_wa_crypt_tools()

    def _check_wa_crypt_tools(self) -> bool:
        """Check if wa-crypt-tools is available."""
        try:
            import wa_crypt_tools
            return True
        except ImportError:
            logger.warning('wa-crypt-tools not installed. Install with: pip install wa-crypt-tools')
            return False

    def load_key(self, key_path: str) -> bool:
        """
        Load decryption key from file.

        Args:
            key_path: Path to key file

        Returns:
            True if key loaded successfully
        """
        success, msg = self.key_extractor.load_key_file(key_path)
        if not success:
            logger.error(f'Failed to load key: {msg}')
        return success

    def detect_format(self, backup_path: str) -> Optional[str]:
        """
        Detect backup format from file header/extension.

        Args:
            backup_path: Path to backup file

        Returns:
            Format string ('crypt14', 'crypt15', 'crypt12', etc.) or None
        """
        path = Path(backup_path)

        # Check extension first
        suffix = path.suffix.lower()
        if suffix in ['.crypt14', '.crypt15', '.crypt12']:
            return suffix[1:]  # Remove dot

        # Try to detect from header
        try:
            with open(backup_path, 'rb') as f:
                header = f.read(100)

            # crypt14 magic bytes
            if len(header) >= 67:
                if header[0:3] == b'\x00\x01\x01':  # crypt14 marker
                    return 'crypt14'
                elif header[0:3] == b'\x00\x01\x02':  # crypt15 marker
                    return 'crypt15'

            # Check for older formats
            if b'SQLite' in header[:50]:
                return 'unencrypted'

        except Exception as e:
            logger.error(f'Format detection failed: {e}')

        return None

    def decrypt(self, backup_path: str, output_dir: str,
                key_path: Optional[str] = None) -> DecryptionResult:
        """
        Decrypt WhatsApp backup file.

        Args:
            backup_path: Path to encrypted backup file
            output_dir: Directory to write decrypted database
            key_path: Optional path to key file (uses loaded key if not provided)

        Returns:
            DecryptionResult with success status and output path
        """
        # Load key if provided
        if key_path:
            if not self.load_key(key_path):
                return DecryptionResult(
                    success=False,
                    error='Failed to load key file'
                )

        # Check key is loaded
        if not self.key_extractor.key_data:
            return DecryptionResult(
                success=False,
                error='No key loaded. Call load_key() first.'
            )

        # Detect format
        format_version = self.detect_format(backup_path)
        if not format_version:
            return DecryptionResult(
                success=False,
                error='Could not detect backup format'
            )

        # Ensure output directory exists
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # Dispatch to appropriate decryption method
        if format_version == 'crypt14':
            return self._decrypt_crypt14(backup_path, output_dir)
        elif format_version == 'crypt15':
            return self._decrypt_crypt15(backup_path, output_dir)
        elif format_version == 'unencrypted':
            # Just copy the file
            import shutil
            output_path = Path(output_dir) / 'msgstore.db'
            shutil.copy2(backup_path, output_path)
            return DecryptionResult(
                success=True,
                output_path=str(output_path),
                format_version='unencrypted'
            )
        else:
            return DecryptionResult(
                success=False,
                error=f'Unsupported format: {format_version}'
            )

    def _decrypt_crypt14(self, backup_path: str, output_dir: str) -> DecryptionResult:
        """
        Decrypt crypt14 format backup.

        crypt14 structure:
        - Header (67 bytes): version info, server salt, google ID hash
        - IV (16 bytes): at offset 51
        - Encrypted data: AES-256-GCM encrypted
        - Auth tag (16 bytes): at end
        """
        try:
            # Try wa-crypt-tools first
            if self._wa_crypt_available:
                return self._decrypt_with_wa_crypt(backup_path, output_dir, 'crypt14')

            # Manual decryption fallback
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM

            key_data = self.key_extractor.key_data

            # Read backup file
            with open(backup_path, 'rb') as f:
                backup_data = f.read()

            # Extract components
            header = backup_data[:self.CRYPT14_HEADER_SIZE]
            iv = header[self.CRYPT14_IV_OFFSET:self.CRYPT14_IV_OFFSET + self.CRYPT14_IV_SIZE]
            ciphertext = backup_data[self.CRYPT14_HEADER_SIZE:-16]  # Exclude auth tag
            auth_tag = backup_data[-16:]

            # Extract encryption key from key file
            # Key file format: [3 bytes skip][32 bytes key][rest...]
            aes_key = key_data[self.CRYPT14_KEY_OFFSET:self.CRYPT14_KEY_OFFSET + 32]

            # Decrypt using AES-256-GCM
            aesgcm = AESGCM(aes_key)

            # Combine ciphertext and tag for GCM
            encrypted_with_tag = ciphertext + auth_tag

            # Use header as AAD (additional authenticated data)
            plaintext = aesgcm.decrypt(iv, encrypted_with_tag, header)

            # Decompress if zlib compressed
            import zlib
            try:
                plaintext = zlib.decompress(plaintext)
            except zlib.error:
                pass  # Not compressed

            # Write decrypted database
            output_path = Path(output_dir) / 'msgstore.db'
            with open(output_path, 'wb') as f:
                f.write(plaintext)

            return DecryptionResult(
                success=True,
                output_path=str(output_path),
                format_version='crypt14',
                metadata={
                    'encrypted_size': len(backup_data),
                    'decrypted_size': len(plaintext)
                }
            )

        except Exception as e:
            logger.error(f'crypt14 decryption failed: {e}')
            return DecryptionResult(
                success=False,
                error=str(e),
                format_version='crypt14'
            )

    def _decrypt_crypt15(self, backup_path: str, output_dir: str) -> DecryptionResult:
        """
        Decrypt crypt15 format backup.

        crypt15 uses a different key derivation with Google account integration.
        Requires: encrypted_backup.key file (158 bytes)
        """
        try:
            if self._wa_crypt_available:
                return self._decrypt_with_wa_crypt(backup_path, output_dir, 'crypt15')

            return DecryptionResult(
                success=False,
                error='crypt15 decryption requires wa-crypt-tools. Install with: pip install wa-crypt-tools',
                format_version='crypt15'
            )

        except Exception as e:
            logger.error(f'crypt15 decryption failed: {e}')
            return DecryptionResult(
                success=False,
                error=str(e),
                format_version='crypt15'
            )

    def _decrypt_with_wa_crypt(self, backup_path: str, output_dir: str,
                               format_version: str) -> DecryptionResult:
        """
        Use wa-crypt-tools library for decryption.

        This is the preferred method as it handles all edge cases.
        """
        try:
            from wa_crypt_tools.lib.db.db14 import Database14
            from wa_crypt_tools.lib.db.db15 import Database15
            from wa_crypt_tools.lib.key.key14 import Key14
            from wa_crypt_tools.lib.key.key15 import Key15

            key_data = self.key_extractor.key_data
            output_path = Path(output_dir) / 'msgstore.db'

            if format_version == 'crypt14':
                # Create key object
                key = Key14(key_data)

                # Create database object and decrypt
                with open(backup_path, 'rb') as f:
                    db = Database14(f, key)

                with open(output_path, 'wb') as f:
                    db.decrypt(f)

            elif format_version == 'crypt15':
                # crypt15 requires encrypted key file
                key = Key15(key_data)

                with open(backup_path, 'rb') as f:
                    db = Database15(f, key)

                with open(output_path, 'wb') as f:
                    db.decrypt(f)

            return DecryptionResult(
                success=True,
                output_path=str(output_path),
                format_version=format_version
            )

        except ImportError as e:
            logger.error(f'wa-crypt-tools import error: {e}')
            return DecryptionResult(
                success=False,
                error=f'wa-crypt-tools module error: {str(e)}'
            )
        except Exception as e:
            logger.error(f'wa-crypt-tools decryption failed: {e}')
            return DecryptionResult(
                success=False,
                error=str(e),
                format_version=format_version
            )


def decrypt_whatsapp_backup(backup_path: str, key_path: str,
                            output_dir: str) -> DecryptionResult:
    """
    Convenience function to decrypt WhatsApp backup.

    Args:
        backup_path: Path to encrypted backup (msgstore.db.crypt14 or crypt15)
        key_path: Path to key file
        output_dir: Directory to write decrypted database

    Returns:
        DecryptionResult with status and output path
    """
    decryptor = WhatsAppBackupDecryptor()
    return decryptor.decrypt(backup_path, output_dir, key_path)


# CLI interface for testing
if __name__ == '__main__':
    import sys

    if len(sys.argv) < 4:
        print('Usage: python whatsapp_decrypt.py <backup_file> <key_file> <output_dir>')
        sys.exit(1)

    backup_file = sys.argv[1]
    key_file = sys.argv[2]
    output_dir = sys.argv[3]

    result = decrypt_whatsapp_backup(backup_file, key_file, output_dir)

    if result.success:
        print(f'Decryption successful!')
        print(f'Output: {result.output_path}')
        print(f'Format: {result.format_version}')
    else:
        print(f'Decryption failed: {result.error}')
        sys.exit(1)
