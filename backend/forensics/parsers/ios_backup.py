"""
iOS Backup Parser for SafeChild Forensics
Parses iTunes/Finder backup files from iOS devices

Supports:
- WhatsApp (ChatStorage.sqlite)
- SMS/iMessage (sms.db)
- Contacts (AddressBook.sqlitedb)
- Call History (CallHistory.storedata)
- Photos metadata

Uses only stdlib: plistlib, sqlite3
"""

import os
import sqlite3
import plistlib
import hashlib
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class iOSBackupParser:
    """
    Parser for unencrypted iOS backups created by iTunes/Finder.

    Backup structure:
    - Manifest.db: SQLite database mapping files
    - Manifest.plist: Backup metadata
    - Info.plist: Device info
    - Status.plist: Backup status
    - Files in 2-character hash directories (aa/, ab/, etc.)
    """

    # Known file domain/path mappings
    KNOWN_FILES = {
        'whatsapp_chats': ('AppDomainGroup-group.net.whatsapp.WhatsApp.shared',
                           'ChatStorage.sqlite'),
        'whatsapp_contacts': ('AppDomainGroup-group.net.whatsapp.WhatsApp.shared',
                              'ContactsV2.sqlite'),
        'sms': ('HomeDomain', 'Library/SMS/sms.db'),
        'contacts': ('HomeDomain', 'Library/AddressBook/AddressBook.sqlitedb'),
        'call_history': ('HomeDomain', 'Library/CallHistoryDB/CallHistory.storedata'),
        'safari_history': ('HomeDomain', 'Library/Safari/History.db'),
        'notes': ('HomeDomain', 'Library/Notes/notes.sqlite'),
        'photos': ('CameraRollDomain', 'Media/DCIM'),
    }

    # Apple's Cocoa epoch (2001-01-01) offset from Unix epoch
    APPLE_EPOCH_OFFSET = 978307200

    def __init__(self, backup_path: str):
        """
        Initialize parser with backup directory path.

        Args:
            backup_path: Path to iOS backup directory
        """
        self.backup_path = Path(backup_path)
        self.manifest_db_path = self.backup_path / 'Manifest.db'
        self.manifest_plist_path = self.backup_path / 'Manifest.plist'
        self.info_plist_path = self.backup_path / 'Info.plist'

        self.device_info: Dict[str, Any] = {}
        self.file_map: Dict[str, str] = {}  # relativePath -> fileID

        self._validate_backup()

    def _validate_backup(self) -> None:
        """Validate that the backup directory structure is correct."""
        if not self.backup_path.exists():
            raise ValueError(f"Backup path does not exist: {self.backup_path}")

        if not self.manifest_db_path.exists():
            raise ValueError(f"Manifest.db not found - not a valid iOS backup")

        if not self.info_plist_path.exists():
            raise ValueError(f"Info.plist not found - not a valid iOS backup")

    def parse_device_info(self) -> Dict[str, Any]:
        """
        Parse device information from Info.plist.

        Returns:
            Dictionary with device details
        """
        try:
            with open(self.info_plist_path, 'rb') as f:
                info = plistlib.load(f)

            self.device_info = {
                'device_name': info.get('Device Name', 'Unknown'),
                'product_type': info.get('Product Type', 'Unknown'),
                'product_version': info.get('Product Version', 'Unknown'),
                'build_version': info.get('Build Version', 'Unknown'),
                'serial_number': info.get('Serial Number', 'Unknown'),
                'unique_device_id': info.get('Unique Device ID', 'Unknown'),
                'phone_number': info.get('Phone Number', 'Unknown'),
                'last_backup_date': info.get('Last Backup Date'),
                'itunes_version': info.get('iTunes Version', 'Unknown'),
                'installed_applications': info.get('Installed Applications', []),
            }

            logger.info(f"Parsed device info: {self.device_info['device_name']} "
                       f"iOS {self.device_info['product_version']}")

            return self.device_info

        except Exception as e:
            logger.error(f"Failed to parse Info.plist: {e}")
            raise

    def build_file_map(self) -> Dict[str, str]:
        """
        Build a mapping of relative paths to file IDs from Manifest.db.

        Returns:
            Dictionary mapping relativePath -> fileID
        """
        try:
            conn = sqlite3.connect(str(self.manifest_db_path))
            cursor = conn.cursor()

            cursor.execute("""
                SELECT fileID, domain, relativePath
                FROM Files
                WHERE flags = 1
            """)

            for file_id, domain, relative_path in cursor.fetchall():
                full_path = f"{domain}/{relative_path}"
                self.file_map[full_path] = file_id

            conn.close()
            logger.info(f"Built file map with {len(self.file_map)} entries")

            return self.file_map

        except Exception as e:
            logger.error(f"Failed to build file map: {e}")
            raise

    def get_file_path(self, domain: str, relative_path: str) -> Optional[Path]:
        """
        Get the actual file path for a given domain/relativePath.

        Args:
            domain: File domain (e.g., 'HomeDomain')
            relative_path: Relative path within domain

        Returns:
            Path to the actual file, or None if not found
        """
        if not self.file_map:
            self.build_file_map()

        full_path = f"{domain}/{relative_path}"
        file_id = self.file_map.get(full_path)

        if not file_id:
            logger.warning(f"File not found in manifest: {full_path}")
            return None

        # Files are stored in 2-char subdirectories
        actual_path = self.backup_path / file_id[:2] / file_id

        if not actual_path.exists():
            logger.warning(f"File exists in manifest but not on disk: {actual_path}")
            return None

        return actual_path

    def extract_file_to_temp(self, domain: str, relative_path: str,
                             temp_dir: str) -> Optional[Path]:
        """
        Extract a file from backup to a temporary directory.

        Args:
            domain: File domain
            relative_path: Relative path within domain
            temp_dir: Temporary directory to extract to

        Returns:
            Path to extracted file, or None if not found
        """
        source_path = self.get_file_path(domain, relative_path)
        if not source_path:
            return None

        # Create temp directory if needed
        temp_path = Path(temp_dir)
        temp_path.mkdir(parents=True, exist_ok=True)

        # Copy with original filename
        dest_path = temp_path / Path(relative_path).name
        shutil.copy2(source_path, dest_path)

        return dest_path

    def _convert_apple_timestamp(self, timestamp: float) -> Optional[datetime]:
        """Convert Apple Cocoa timestamp to datetime."""
        if timestamp is None or timestamp == 0:
            return None
        try:
            unix_timestamp = timestamp + self.APPLE_EPOCH_OFFSET
            return datetime.fromtimestamp(unix_timestamp)
        except (ValueError, OSError):
            return None

    def parse_sms(self, limit: int = 10000) -> List[Dict[str, Any]]:
        """
        Parse SMS/iMessage from sms.db.

        Args:
            limit: Maximum number of messages to return

        Returns:
            List of message dictionaries
        """
        messages = []

        db_path = self.get_file_path('HomeDomain', 'Library/SMS/sms.db')
        if not db_path:
            logger.warning("SMS database not found in backup")
            return messages

        try:
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    m.ROWID as id,
                    m.text,
                    m.date / 1000000000 as date_timestamp,
                    m.is_from_me,
                    m.is_read,
                    m.service,
                    h.id as handle_id,
                    h.uncanonicalized_id as phone_number
                FROM message m
                LEFT JOIN handle h ON m.handle_id = h.ROWID
                ORDER BY m.date DESC
                LIMIT ?
            """, (limit,))

            for row in cursor.fetchall():
                timestamp = self._convert_apple_timestamp(row['date_timestamp'])

                messages.append({
                    'id': row['id'],
                    'text': row['text'],
                    'timestamp': timestamp.isoformat() if timestamp else None,
                    'is_from_me': bool(row['is_from_me']),
                    'is_read': bool(row['is_read']),
                    'service': row['service'],  # 'SMS' or 'iMessage'
                    'phone_number': row['phone_number'],
                    'platform': 'ios_sms'
                })

            conn.close()
            logger.info(f"Parsed {len(messages)} SMS/iMessage messages")

        except Exception as e:
            logger.error(f"Failed to parse SMS database: {e}")

        return messages

    def parse_contacts(self) -> List[Dict[str, Any]]:
        """
        Parse contacts from AddressBook.sqlitedb.

        Returns:
            List of contact dictionaries
        """
        contacts = []

        db_path = self.get_file_path('HomeDomain',
                                      'Library/AddressBook/AddressBook.sqlitedb')
        if not db_path:
            logger.warning("Contacts database not found in backup")
            return contacts

        try:
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Get all people
            cursor.execute("""
                SELECT
                    ROWID,
                    First as first_name,
                    Last as last_name,
                    Organization as organization,
                    Note as note,
                    CreationDate as created,
                    ModificationDate as modified
                FROM ABPerson
            """)

            people = {row['ROWID']: dict(row) for row in cursor.fetchall()}

            # Get phone numbers
            cursor.execute("""
                SELECT record_id, value, label
                FROM ABMultiValue
                WHERE property = 3
            """)

            for row in cursor.fetchall():
                record_id = row['record_id']
                if record_id in people:
                    if 'phones' not in people[record_id]:
                        people[record_id]['phones'] = []
                    people[record_id]['phones'].append({
                        'number': row['value'],
                        'label': row['label']
                    })

            # Get emails
            cursor.execute("""
                SELECT record_id, value, label
                FROM ABMultiValue
                WHERE property = 4
            """)

            for row in cursor.fetchall():
                record_id = row['record_id']
                if record_id in people:
                    if 'emails' not in people[record_id]:
                        people[record_id]['emails'] = []
                    people[record_id]['emails'].append({
                        'email': row['value'],
                        'label': row['label']
                    })

            # Format output
            for person_id, person in people.items():
                contacts.append({
                    'id': person_id,
                    'first_name': person.get('first_name'),
                    'last_name': person.get('last_name'),
                    'organization': person.get('organization'),
                    'phones': person.get('phones', []),
                    'emails': person.get('emails', []),
                    'note': person.get('note'),
                    'platform': 'ios_contacts'
                })

            conn.close()
            logger.info(f"Parsed {len(contacts)} contacts")

        except Exception as e:
            logger.error(f"Failed to parse contacts database: {e}")

        return contacts

    def parse_call_history(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Parse call history from CallHistory.storedata.

        Args:
            limit: Maximum number of calls to return

        Returns:
            List of call dictionaries
        """
        calls = []

        db_path = self.get_file_path('HomeDomain',
                                      'Library/CallHistoryDB/CallHistory.storedata')
        if not db_path:
            logger.warning("Call history database not found in backup")
            return calls

        try:
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    Z_PK as id,
                    ZADDRESS as phone_number,
                    ZDURATION as duration,
                    ZDATE as date_timestamp,
                    ZORIGINATED as is_outgoing,
                    ZANSWERED as was_answered,
                    ZCALLTYPE as call_type
                FROM ZCALLRECORD
                ORDER BY ZDATE DESC
                LIMIT ?
            """, (limit,))

            for row in cursor.fetchall():
                timestamp = self._convert_apple_timestamp(row['date_timestamp'])

                # Determine call direction and status
                if row['is_outgoing']:
                    direction = 'outgoing'
                elif row['was_answered']:
                    direction = 'incoming'
                else:
                    direction = 'missed'

                calls.append({
                    'id': row['id'],
                    'phone_number': row['phone_number'],
                    'duration_seconds': row['duration'],
                    'timestamp': timestamp.isoformat() if timestamp else None,
                    'direction': direction,
                    'call_type': row['call_type'],
                    'platform': 'ios_calls'
                })

            conn.close()
            logger.info(f"Parsed {len(calls)} call records")

        except Exception as e:
            logger.error(f"Failed to parse call history: {e}")

        return calls

    def parse_whatsapp(self, limit: int = 10000) -> List[Dict[str, Any]]:
        """
        Parse WhatsApp messages from iOS backup.

        Args:
            limit: Maximum number of messages to return

        Returns:
            List of message dictionaries
        """
        messages = []

        # WhatsApp stores data in app group container
        db_path = self.get_file_path(
            'AppDomainGroup-group.net.whatsapp.WhatsApp.shared',
            'ChatStorage.sqlite'
        )

        if not db_path:
            logger.warning("WhatsApp database not found in backup")
            return messages

        try:
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    m.Z_PK as id,
                    m.ZTEXT as text,
                    m.ZMESSAGEDATE as date_timestamp,
                    m.ZISFROMME as is_from_me,
                    m.ZMEDIAITEM as has_media,
                    c.ZCONTACTJID as contact_jid,
                    c.ZPARTNERNAME as contact_name
                FROM ZWAMESSAGE m
                JOIN ZWACHATSESSION c ON m.ZCHATSESSION = c.Z_PK
                ORDER BY m.ZMESSAGEDATE DESC
                LIMIT ?
            """, (limit,))

            for row in cursor.fetchall():
                timestamp = self._convert_apple_timestamp(row['date_timestamp'])

                # Extract phone number from JID
                jid = row['contact_jid'] or ''
                phone = jid.split('@')[0] if '@' in jid else jid

                messages.append({
                    'id': row['id'],
                    'text': row['text'],
                    'timestamp': timestamp.isoformat() if timestamp else None,
                    'is_from_me': bool(row['is_from_me']),
                    'has_media': bool(row['has_media']),
                    'phone_number': phone,
                    'contact_name': row['contact_name'],
                    'platform': 'whatsapp_ios'
                })

            conn.close()
            logger.info(f"Parsed {len(messages)} WhatsApp messages from iOS")

        except Exception as e:
            logger.error(f"Failed to parse WhatsApp iOS database: {e}")

        return messages

    def get_backup_summary(self) -> Dict[str, Any]:
        """
        Get a summary of what's available in this backup.

        Returns:
            Dictionary with backup summary
        """
        if not self.device_info:
            self.parse_device_info()

        if not self.file_map:
            self.build_file_map()

        # Check what's available
        available = {}
        for key, (domain, path) in self.KNOWN_FILES.items():
            full_path = f"{domain}/{path}"
            available[key] = any(full_path in fp for fp in self.file_map.keys())

        return {
            'device_info': self.device_info,
            'total_files': len(self.file_map),
            'available_data': available,
            'backup_date': self.device_info.get('last_backup_date'),
        }

    def extract_all(self, output_dir: str) -> Dict[str, Any]:
        """
        Extract all available data from the backup.

        Args:
            output_dir: Directory to store extracted data

        Returns:
            Dictionary with all extracted data
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        result = {
            'device_info': self.parse_device_info(),
            'sms': self.parse_sms(),
            'contacts': self.parse_contacts(),
            'call_history': self.parse_call_history(),
            'whatsapp': self.parse_whatsapp(),
        }

        # Write summary
        summary = self.get_backup_summary()
        summary['extracted'] = {
            'sms_count': len(result['sms']),
            'contacts_count': len(result['contacts']),
            'calls_count': len(result['call_history']),
            'whatsapp_count': len(result['whatsapp']),
        }

        logger.info(f"Extraction complete: {summary['extracted']}")

        return result


def detect_ios_backup(path: str) -> bool:
    """
    Check if a directory is a valid iOS backup.

    Args:
        path: Path to check

    Returns:
        True if valid iOS backup
    """
    backup_path = Path(path)

    required_files = ['Manifest.db', 'Info.plist']
    return all((backup_path / f).exists() for f in required_files)
