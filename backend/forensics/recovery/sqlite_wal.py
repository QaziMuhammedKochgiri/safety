"""
SQLite WAL (Write-Ahead Log) Recovery Module for SafeChild Forensics

Recovers deleted messages and data from SQLite databases using:
- WAL (Write-Ahead Log) parsing
- Journal file analysis
- Freelist page scanning
- Deleted row recovery from table pages

References:
- SQLite WAL Format: https://sqlite.org/walformat.html
- SQLite File Format: https://sqlite.org/fileformat.html
"""

import os
import struct
import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
import hashlib
import logging

logger = logging.getLogger(__name__)

# SQLite constants
SQLITE_HEADER_SIZE = 100
SQLITE_PAGE_SIZE_OFFSET = 16
WAL_HEADER_SIZE = 32
WAL_FRAME_HEADER_SIZE = 24


class SQLiteWALRecovery:
    """
    Recovers deleted data from SQLite databases using WAL analysis.

    Supports:
    - WhatsApp msgstore.db
    - iOS sms.db
    - Signal database
    - Any SQLite database with WAL mode
    """

    def __init__(self, db_path: str):
        """
        Initialize recovery module.

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = Path(db_path)
        self.wal_path = Path(f"{db_path}-wal")
        self.shm_path = Path(f"{db_path}-shm")
        self.journal_path = Path(f"{db_path}-journal")

        self.page_size = 4096  # Default, will be updated
        self.recovered_records: List[Dict[str, Any]] = []

    def check_wal_exists(self) -> Dict[str, bool]:
        """Check which recovery files exist."""
        return {
            'database': self.db_path.exists(),
            'wal': self.wal_path.exists(),
            'shm': self.shm_path.exists(),
            'journal': self.journal_path.exists()
        }

    def get_page_size(self) -> int:
        """Read page size from database header."""
        try:
            with open(self.db_path, 'rb') as f:
                f.seek(SQLITE_PAGE_SIZE_OFFSET)
                page_size_bytes = f.read(2)
                page_size = struct.unpack('>H', page_size_bytes)[0]

                # Page size of 1 means 65536
                if page_size == 1:
                    page_size = 65536

                self.page_size = page_size
                return page_size

        except Exception as e:
            logger.error(f"Failed to read page size: {e}")
            return self.page_size

    def parse_wal_header(self) -> Optional[Dict[str, Any]]:
        """
        Parse WAL file header.

        Returns:
            Dictionary with WAL header info or None if invalid
        """
        if not self.wal_path.exists():
            return None

        try:
            with open(self.wal_path, 'rb') as f:
                header = f.read(WAL_HEADER_SIZE)

                if len(header) < WAL_HEADER_SIZE:
                    return None

                magic = struct.unpack('>I', header[0:4])[0]
                file_format = struct.unpack('>I', header[4:8])[0]
                page_size = struct.unpack('>I', header[8:12])[0]
                checkpoint_seq = struct.unpack('>I', header[12:16])[0]
                salt1 = struct.unpack('>I', header[16:20])[0]
                salt2 = struct.unpack('>I', header[20:24])[0]
                checksum1 = struct.unpack('>I', header[24:28])[0]
                checksum2 = struct.unpack('>I', header[28:32])[0]

                # Validate magic number (0x377f0682 or 0x377f0683)
                if magic not in (0x377f0682, 0x377f0683):
                    logger.warning(f"Invalid WAL magic number: {hex(magic)}")
                    return None

                self.page_size = page_size

                return {
                    'magic': hex(magic),
                    'format': file_format,
                    'page_size': page_size,
                    'checkpoint_seq': checkpoint_seq,
                    'salt1': salt1,
                    'salt2': salt2,
                    'valid': True
                }

        except Exception as e:
            logger.error(f"Failed to parse WAL header: {e}")
            return None

    def extract_wal_frames(self) -> List[Dict[str, Any]]:
        """
        Extract all frames from WAL file.

        Returns:
            List of frame dictionaries with page data
        """
        frames = []

        if not self.wal_path.exists():
            return frames

        try:
            with open(self.wal_path, 'rb') as f:
                # Read WAL header
                f.read(WAL_HEADER_SIZE)

                frame_num = 0
                while True:
                    # Read frame header
                    frame_header = f.read(WAL_FRAME_HEADER_SIZE)
                    if len(frame_header) < WAL_FRAME_HEADER_SIZE:
                        break

                    page_number = struct.unpack('>I', frame_header[0:4])[0]
                    commit_size = struct.unpack('>I', frame_header[4:8])[0]
                    salt1 = struct.unpack('>I', frame_header[8:12])[0]
                    salt2 = struct.unpack('>I', frame_header[12:16])[0]
                    checksum1 = struct.unpack('>I', frame_header[16:20])[0]
                    checksum2 = struct.unpack('>I', frame_header[20:24])[0]

                    # Read page data
                    page_data = f.read(self.page_size)
                    if len(page_data) < self.page_size:
                        break

                    frames.append({
                        'frame_number': frame_num,
                        'page_number': page_number,
                        'commit_size': commit_size,
                        'data': page_data,
                        'data_hash': hashlib.md5(page_data).hexdigest()
                    })

                    frame_num += 1

            logger.info(f"Extracted {len(frames)} WAL frames")
            return frames

        except Exception as e:
            logger.error(f"Failed to extract WAL frames: {e}")
            return frames

    def scan_page_for_deleted_records(self, page_data: bytes,
                                       table_name: str = None) -> List[Dict[str, Any]]:
        """
        Scan a page for potentially deleted records.

        Args:
            page_data: Raw page bytes
            table_name: Optional table name for context

        Returns:
            List of recovered record candidates
        """
        records = []

        try:
            # Page type is first byte
            page_type = page_data[0]

            # B-tree leaf table page = 0x0d
            # B-tree interior table page = 0x05
            # B-tree leaf index page = 0x0a
            # B-tree interior index page = 0x02

            if page_type not in (0x0d, 0x05, 0x0a, 0x02):
                return records

            # For leaf table pages, scan for cell content
            if page_type == 0x0d:
                # First freeblock offset at bytes 1-2
                first_freeblock = struct.unpack('>H', page_data[1:3])[0]

                # Number of cells at bytes 3-4
                num_cells = struct.unpack('>H', page_data[3:5])[0]

                # Cell content area start at bytes 5-6
                cell_start = struct.unpack('>H', page_data[5:7])[0]

                # Scan freeblocks for deleted content
                if first_freeblock > 0:
                    freeblock_offset = first_freeblock

                    while freeblock_offset > 0 and freeblock_offset < len(page_data) - 4:
                        # Next freeblock offset
                        next_freeblock = struct.unpack('>H',
                            page_data[freeblock_offset:freeblock_offset+2])[0]

                        # Freeblock size
                        block_size = struct.unpack('>H',
                            page_data[freeblock_offset+2:freeblock_offset+4])[0]

                        if block_size > 4 and block_size < 1000:
                            # Extract freeblock content
                            content = page_data[freeblock_offset+4:freeblock_offset+block_size]

                            # Try to find text content
                            text_content = self._extract_text_from_bytes(content)

                            if text_content:
                                records.append({
                                    'type': 'deleted_freeblock',
                                    'offset': freeblock_offset,
                                    'size': block_size,
                                    'content': text_content,
                                    'table': table_name,
                                    'confidence': 0.6
                                })

                        freeblock_offset = next_freeblock

        except Exception as e:
            logger.debug(f"Error scanning page: {e}")

        return records

    def _extract_text_from_bytes(self, data: bytes) -> Optional[str]:
        """
        Try to extract readable text from bytes.

        Args:
            data: Raw bytes

        Returns:
            Extracted text or None
        """
        try:
            # Try UTF-8 first
            text = data.decode('utf-8', errors='ignore')
            text = ''.join(c for c in text if c.isprintable() or c in '\n\r\t')

            # Filter out garbage - must have some readable content
            if len(text) > 5 and any(c.isalpha() for c in text):
                return text.strip()

        except Exception:
            pass

        return None

    def recover_deleted_messages(self, message_table: str = 'messages',
                                  text_column: str = 'text') -> List[Dict[str, Any]]:
        """
        Attempt to recover deleted messages from WAL and database.

        Args:
            message_table: Name of the message table
            text_column: Name of the text column

        Returns:
            List of recovered message records
        """
        recovered = []

        # First try WAL frames
        wal_frames = self.extract_wal_frames()

        for frame in wal_frames:
            page_records = self.scan_page_for_deleted_records(
                frame['data'],
                table_name=message_table
            )

            for record in page_records:
                record['source'] = 'wal'
                record['frame_number'] = frame['frame_number']
                recovered.append(record)

        # Then scan database freelist
        try:
            conn = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True)
            cursor = conn.cursor()

            # Get freelist pages
            cursor.execute("PRAGMA freelist_count")
            freelist_count = cursor.fetchone()[0]

            if freelist_count > 0:
                logger.info(f"Found {freelist_count} freelist pages to scan")

                # Read raw database for freelist pages
                with open(self.db_path, 'rb') as f:
                    # Get total pages
                    f.seek(28)
                    total_pages = struct.unpack('>I', f.read(4))[0]

                    # Get first freelist trunk page
                    f.seek(32)
                    first_freelist = struct.unpack('>I', f.read(4))[0]

                    # Scan freelist pages
                    current_page = first_freelist
                    visited = set()

                    while current_page > 0 and current_page not in visited:
                        visited.add(current_page)

                        # Seek to page
                        page_offset = (current_page - 1) * self.page_size
                        f.seek(page_offset)
                        page_data = f.read(self.page_size)

                        # Scan for deleted records
                        page_records = self.scan_page_for_deleted_records(
                            page_data,
                            table_name=message_table
                        )

                        for record in page_records:
                            record['source'] = 'freelist'
                            record['page_number'] = current_page
                            recovered.append(record)

                        # Next trunk page is at offset 0
                        next_trunk = struct.unpack('>I', page_data[0:4])[0]
                        current_page = next_trunk

            conn.close()

        except Exception as e:
            logger.error(f"Error scanning freelist: {e}")

        self.recovered_records = recovered
        logger.info(f"Recovered {len(recovered)} potential deleted records")

        return recovered

    def get_recovery_summary(self) -> Dict[str, Any]:
        """Get summary of recovery analysis."""
        files = self.check_wal_exists()
        wal_header = self.parse_wal_header()

        return {
            'database_path': str(self.db_path),
            'files_found': files,
            'wal_header': wal_header,
            'page_size': self.page_size,
            'recovered_count': len(self.recovered_records),
            'recovery_sources': {
                'wal': len([r for r in self.recovered_records if r.get('source') == 'wal']),
                'freelist': len([r for r in self.recovered_records if r.get('source') == 'freelist'])
            }
        }


class WhatsAppRecovery(SQLiteWALRecovery):
    """
    Specialized recovery for WhatsApp databases.
    """

    def __init__(self, db_path: str):
        super().__init__(db_path)

    def recover_whatsapp_messages(self) -> List[Dict[str, Any]]:
        """Recover deleted WhatsApp messages."""
        # WhatsApp uses 'messages' table with 'data' column for text
        return self.recover_deleted_messages(
            message_table='messages',
            text_column='data'
        )


class SMSRecovery(SQLiteWALRecovery):
    """
    Specialized recovery for iOS SMS database.
    """

    def __init__(self, db_path: str):
        super().__init__(db_path)

    def recover_sms_messages(self) -> List[Dict[str, Any]]:
        """Recover deleted SMS/iMessage."""
        # iOS uses 'message' table with 'text' column
        return self.recover_deleted_messages(
            message_table='message',
            text_column='text'
        )


def analyze_database_for_recovery(db_path: str) -> Dict[str, Any]:
    """
    Analyze a database and attempt recovery.

    Args:
        db_path: Path to SQLite database

    Returns:
        Dictionary with analysis results
    """
    recovery = SQLiteWALRecovery(db_path)

    # Get page size first
    recovery.get_page_size()

    # Check what's available
    files = recovery.check_wal_exists()

    # Parse WAL if exists
    wal_info = recovery.parse_wal_header()

    # Attempt recovery
    recovered = recovery.recover_deleted_messages()

    # Get summary
    summary = recovery.get_recovery_summary()
    summary['recovered_records'] = recovered

    return summary
