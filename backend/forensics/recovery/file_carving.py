"""
File Carving Module for Digital Forensics

Recovers deleted files by scanning for file signatures (magic bytes).
Supports JPEG, PNG, GIF, PDF, MP4, and common document formats.

Useful for:
- Recovering deleted photos/videos
- Finding embedded/hidden images
- Extracting media from unallocated disk space
- Forensic image analysis

Uses Python stdlib only - no external dependencies required.
"""

import os
import struct
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Generator
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class FileType(Enum):
    """Supported file types for carving."""
    JPEG = "jpeg"
    PNG = "png"
    GIF = "gif"
    PDF = "pdf"
    MP4 = "mp4"
    ZIP = "zip"
    SQLITE = "sqlite"
    WEBP = "webp"
    HEIC = "heic"
    BMP = "bmp"


@dataclass
class FileSignature:
    """File signature definition for carving."""
    file_type: FileType
    header: bytes
    footer: Optional[bytes] = None
    extension: str = ""
    max_size: int = 50 * 1024 * 1024  # 50MB default max
    header_offset: int = 0


@dataclass
class CarvedFile:
    """Represents a carved/recovered file."""
    file_type: FileType
    offset: int
    size: int
    md5_hash: str
    output_path: Optional[str] = None
    confidence: float = 1.0
    metadata: Dict = field(default_factory=dict)


# File signature definitions
FILE_SIGNATURES = [
    # JPEG - FFD8FFE0/E1/E8 header, FFD9 footer
    FileSignature(
        file_type=FileType.JPEG,
        header=b'\xFF\xD8\xFF\xE0',
        footer=b'\xFF\xD9',
        extension='.jpg',
        max_size=30 * 1024 * 1024  # 30MB
    ),
    FileSignature(
        file_type=FileType.JPEG,
        header=b'\xFF\xD8\xFF\xE1',  # EXIF JPEG
        footer=b'\xFF\xD9',
        extension='.jpg',
        max_size=30 * 1024 * 1024
    ),
    FileSignature(
        file_type=FileType.JPEG,
        header=b'\xFF\xD8\xFF\xE8',  # SPIFF JPEG
        footer=b'\xFF\xD9',
        extension='.jpg',
        max_size=30 * 1024 * 1024
    ),

    # PNG - 89504E470D0A1A0A header, IEND footer
    FileSignature(
        file_type=FileType.PNG,
        header=b'\x89PNG\r\n\x1a\n',
        footer=b'IEND\xAE\x42\x60\x82',
        extension='.png',
        max_size=50 * 1024 * 1024
    ),

    # GIF - GIF87a or GIF89a header, 3B footer
    FileSignature(
        file_type=FileType.GIF,
        header=b'GIF89a',
        footer=b'\x00;',  # NUL + semicolon
        extension='.gif',
        max_size=20 * 1024 * 1024
    ),
    FileSignature(
        file_type=FileType.GIF,
        header=b'GIF87a',
        footer=b'\x00;',
        extension='.gif',
        max_size=20 * 1024 * 1024
    ),

    # PDF - %PDF header, %%EOF footer
    FileSignature(
        file_type=FileType.PDF,
        header=b'%PDF-',
        footer=b'%%EOF',
        extension='.pdf',
        max_size=100 * 1024 * 1024  # 100MB
    ),

    # MP4/MOV - ftyp header (various)
    FileSignature(
        file_type=FileType.MP4,
        header=b'\x00\x00\x00\x14ftypisom',
        footer=None,  # Complex structure
        extension='.mp4',
        max_size=500 * 1024 * 1024  # 500MB
    ),
    FileSignature(
        file_type=FileType.MP4,
        header=b'\x00\x00\x00\x18ftypmp42',
        footer=None,
        extension='.mp4',
        max_size=500 * 1024 * 1024
    ),
    FileSignature(
        file_type=FileType.MP4,
        header=b'\x00\x00\x00\x20ftypisom',
        footer=None,
        extension='.mp4',
        max_size=500 * 1024 * 1024
    ),

    # ZIP (also DOCX, XLSX, APK, etc.)
    FileSignature(
        file_type=FileType.ZIP,
        header=b'PK\x03\x04',
        footer=b'PK\x05\x06',
        extension='.zip',
        max_size=200 * 1024 * 1024
    ),

    # SQLite database
    FileSignature(
        file_type=FileType.SQLITE,
        header=b'SQLite format 3\x00',
        footer=None,
        extension='.db',
        max_size=500 * 1024 * 1024
    ),

    # WebP
    FileSignature(
        file_type=FileType.WEBP,
        header=b'RIFF',
        footer=None,
        extension='.webp',
        max_size=30 * 1024 * 1024
    ),

    # BMP
    FileSignature(
        file_type=FileType.BMP,
        header=b'BM',
        footer=None,
        extension='.bmp',
        max_size=30 * 1024 * 1024
    ),
]


class FileCarver:
    """
    File carving engine for recovering deleted files.

    Scans raw data for file signatures and extracts matching files.

    Usage:
        carver = FileCarver(output_dir='/output/recovered')
        results = carver.carve_file('/path/to/disk.img')

        # Or carve from memory
        results = carver.carve_data(raw_bytes)
    """

    def __init__(self, output_dir: str, chunk_size: int = 1024 * 1024):
        """
        Initialize file carver.

        Args:
            output_dir: Directory to save carved files
            chunk_size: Size of chunks to read at a time (1MB default)
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.chunk_size = chunk_size
        self.signatures = FILE_SIGNATURES.copy()

    def add_signature(self, signature: FileSignature):
        """Add custom file signature."""
        self.signatures.append(signature)

    def carve_file(self, input_path: str,
                   file_types: Optional[List[FileType]] = None) -> List[CarvedFile]:
        """
        Carve files from a disk image or file.

        Args:
            input_path: Path to input file (disk image, raw data, etc.)
            file_types: Optional list of file types to look for

        Returns:
            List of CarvedFile objects
        """
        results = []
        input_path = Path(input_path)

        if not input_path.exists():
            logger.error(f"Input file not found: {input_path}")
            return results

        file_size = input_path.stat().st_size
        logger.info(f"Starting carve of {input_path} ({file_size:,} bytes)")

        # Filter signatures if specific types requested
        signatures = self.signatures
        if file_types:
            signatures = [s for s in self.signatures if s.file_type in file_types]

        with open(input_path, 'rb') as f:
            results = self._carve_stream(f, file_size, signatures)

        logger.info(f"Carving complete. Found {len(results)} files")
        return results

    def carve_data(self, data: bytes,
                   file_types: Optional[List[FileType]] = None) -> List[CarvedFile]:
        """
        Carve files from raw bytes.

        Args:
            data: Raw bytes to scan
            file_types: Optional list of file types to look for

        Returns:
            List of CarvedFile objects
        """
        from io import BytesIO

        # Filter signatures if specific types requested
        signatures = self.signatures
        if file_types:
            signatures = [s for s in self.signatures if s.file_type in file_types]

        return self._carve_stream(BytesIO(data), len(data), signatures)

    def _carve_stream(self, stream, total_size: int,
                      signatures: List[FileSignature]) -> List[CarvedFile]:
        """
        Internal carving implementation.

        Uses sliding window approach to find file headers.
        """
        results = []
        carved_count = {ft: 0 for ft in FileType}
        seen_hashes = set()

        # Build header map for fast lookup
        header_map = {}
        for sig in signatures:
            header_len = len(sig.header)
            if header_len not in header_map:
                header_map[header_len] = []
            header_map[header_len].append(sig)

        # Get all header lengths to check
        header_lengths = sorted(header_map.keys(), reverse=True)
        max_header_len = max(header_lengths) if header_lengths else 0

        # Read and scan in chunks with overlap
        offset = 0
        overlap = max_header_len
        prev_chunk_tail = b''

        while offset < total_size:
            # Read chunk
            stream.seek(offset)
            chunk = stream.read(self.chunk_size)

            if not chunk:
                break

            # Combine with previous chunk tail for overlap
            search_data = prev_chunk_tail + chunk
            search_offset = offset - len(prev_chunk_tail)

            # Scan for each header length
            for header_len in header_lengths:
                for sig in header_map[header_len]:
                    # Find all occurrences of this header
                    pos = 0
                    while True:
                        idx = search_data.find(sig.header, pos)
                        if idx == -1:
                            break

                        # Calculate actual file offset
                        file_offset = search_offset + idx

                        # Try to extract the file
                        carved = self._extract_file(stream, file_offset, sig,
                                                    carved_count[sig.file_type])

                        if carved and carved.md5_hash not in seen_hashes:
                            seen_hashes.add(carved.md5_hash)
                            results.append(carved)
                            carved_count[sig.file_type] += 1
                            logger.debug(f"Found {sig.file_type.value} at offset {file_offset}")

                        pos = idx + 1

            # Save tail for next iteration
            prev_chunk_tail = chunk[-overlap:] if len(chunk) >= overlap else chunk
            offset += len(chunk) - overlap if len(chunk) > overlap else len(chunk)

            # Progress logging
            if offset % (10 * 1024 * 1024) == 0:  # Every 10MB
                progress = (offset / total_size) * 100
                logger.debug(f"Carving progress: {progress:.1f}%")

        return results

    def _extract_file(self, stream, offset: int, sig: FileSignature,
                      count: int) -> Optional[CarvedFile]:
        """
        Extract a single file starting at offset.

        Args:
            stream: File stream
            offset: Starting offset of file
            sig: File signature to match
            count: Count for naming

        Returns:
            CarvedFile if successful, None otherwise
        """
        try:
            stream.seek(offset)

            # Read header to verify
            header = stream.read(len(sig.header))
            if header != sig.header:
                return None

            # Seek back to start
            stream.seek(offset)

            # Determine file size
            if sig.footer:
                # Read up to max_size looking for footer
                data = stream.read(sig.max_size)
                footer_pos = data.rfind(sig.footer)

                if footer_pos == -1:
                    # No footer found within max_size
                    return None

                file_size = footer_pos + len(sig.footer)
                file_data = data[:file_size]
            else:
                # No footer - try to determine size from header
                file_size = self._get_file_size(stream, offset, sig)
                if file_size is None or file_size > sig.max_size:
                    file_size = min(sig.max_size, 1024 * 1024)  # Default 1MB

                stream.seek(offset)
                file_data = stream.read(file_size)

            # Validate extracted data
            if not self._validate_file(file_data, sig):
                return None

            # Calculate hash
            md5_hash = hashlib.md5(file_data).hexdigest()

            # Save file
            filename = f"carved_{sig.file_type.value}_{count:04d}_{md5_hash[:8]}{sig.extension}"
            output_path = self.output_dir / filename

            with open(output_path, 'wb') as f:
                f.write(file_data)

            return CarvedFile(
                file_type=sig.file_type,
                offset=offset,
                size=len(file_data),
                md5_hash=md5_hash,
                output_path=str(output_path),
                confidence=0.9 if sig.footer else 0.7
            )

        except Exception as e:
            logger.debug(f"Extraction failed at offset {offset}: {e}")
            return None

    def _get_file_size(self, stream, offset: int, sig: FileSignature) -> Optional[int]:
        """
        Try to determine file size from file structure.

        Some formats like PNG, ZIP store size in header.
        """
        try:
            if sig.file_type == FileType.PNG:
                # PNG chunks have length prefix
                # For simplicity, read a reasonable amount
                return None  # Let footer detection handle it

            elif sig.file_type == FileType.BMP:
                # BMP stores file size at offset 2 (4 bytes, little endian)
                stream.seek(offset + 2)
                size_bytes = stream.read(4)
                return struct.unpack('<I', size_bytes)[0]

            elif sig.file_type == FileType.ZIP:
                # ZIP end of central directory has comment length
                # Complex to parse - use footer detection
                return None

            elif sig.file_type == FileType.SQLITE:
                # SQLite page size at offset 16, page count at offset 28
                stream.seek(offset + 16)
                page_size = struct.unpack('>H', stream.read(2))[0]
                if page_size == 1:
                    page_size = 65536
                stream.seek(offset + 28)
                page_count = struct.unpack('>I', stream.read(4))[0]
                return page_size * page_count

            elif sig.file_type == FileType.MP4:
                # MP4 uses box structure with size prefix
                stream.seek(offset)
                # Read first box size
                box_size = struct.unpack('>I', stream.read(4))[0]
                # Simplified - just return first box or fixed size
                return min(box_size, sig.max_size) if box_size > 8 else None

        except Exception:
            pass

        return None

    def _validate_file(self, data: bytes, sig: FileSignature) -> bool:
        """
        Basic validation of extracted file data.
        """
        if len(data) < 8:
            return False

        # Verify header
        if not data.startswith(sig.header):
            return False

        # Type-specific validation
        if sig.file_type == FileType.JPEG:
            # Check for valid JPEG end
            if len(data) > 10 and not data.endswith(b'\xFF\xD9'):
                return False

        elif sig.file_type == FileType.PNG:
            # Check for IHDR chunk (should be first after signature)
            if len(data) > 20 and b'IHDR' not in data[:24]:
                return False

        elif sig.file_type == FileType.SQLITE:
            # Check for SQLite header string
            if not data.startswith(b'SQLite format 3\x00'):
                return False

        return True


def carve_images_from_file(input_path: str, output_dir: str) -> List[CarvedFile]:
    """
    Convenience function to carve only image files.

    Args:
        input_path: Path to scan
        output_dir: Directory for recovered images

    Returns:
        List of carved image files
    """
    carver = FileCarver(output_dir)
    image_types = [FileType.JPEG, FileType.PNG, FileType.GIF, FileType.WEBP, FileType.BMP]
    return carver.carve_file(input_path, file_types=image_types)


def carve_all_from_file(input_path: str, output_dir: str) -> List[CarvedFile]:
    """
    Carve all supported file types.

    Args:
        input_path: Path to scan
        output_dir: Directory for recovered files

    Returns:
        List of all carved files
    """
    carver = FileCarver(output_dir)
    return carver.carve_file(input_path)


async def carve_deleted_files(source_dir: str, output_dir: str) -> int:
    """
    Async wrapper to scan a directory for recoverable deleted files.

    This scans all files in the source directory for embedded/deleted files
    using file carving techniques.

    Args:
        source_dir: Directory to scan for recoverable files
        output_dir: Directory to save recovered files

    Returns:
        Number of files recovered
    """
    import asyncio
    from pathlib import Path

    source_path = Path(source_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    carver = FileCarver(str(output_path))
    total_recovered = 0

    # Scan files that might contain deleted data
    scannable_extensions = {'.db', '.sqlite', '.bin', '.raw', '.img', '.dat', '.bak'}

    for file_path in source_path.rglob('*'):
        if not file_path.is_file():
            continue

        # Scan database files and raw data files
        if file_path.suffix.lower() in scannable_extensions or file_path.stat().st_size > 1024 * 1024:
            try:
                results = carver.carve_file(str(file_path))
                total_recovered += len(results)

                if results:
                    logger.info(f"Recovered {len(results)} files from {file_path.name}")

            except Exception as e:
                logger.warning(f"Error scanning {file_path}: {e}")

        # Allow other tasks to run
        await asyncio.sleep(0)

    # Also scan for images/media in common locations
    media_dirs = ['DCIM', 'Pictures', 'Camera', 'Media', 'WhatsApp', 'Telegram']
    for media_dir in media_dirs:
        media_path = source_path / media_dir
        if media_path.exists():
            for file_path in media_path.rglob('*'):
                if file_path.is_file() and file_path.stat().st_size > 100:
                    try:
                        # Quick scan for embedded images
                        results = carver.carve_file(str(file_path), file_types=[FileType.JPEG, FileType.PNG])
                        total_recovered += len(results)
                    except Exception:
                        pass
                await asyncio.sleep(0)

    logger.info(f"Total files recovered: {total_recovered}")
    return total_recovered


# CLI interface
if __name__ == '__main__':
    import sys

    if len(sys.argv) < 3:
        print("Usage: python file_carving.py <input_file> <output_dir> [type]")
        print("Types: jpeg, png, gif, pdf, mp4, zip, sqlite, all (default)")
        sys.exit(1)

    input_file = sys.argv[1]
    output_dir = sys.argv[2]
    file_type = sys.argv[3] if len(sys.argv) > 3 else 'all'

    logging.basicConfig(level=logging.INFO)

    if file_type == 'all':
        results = carve_all_from_file(input_file, output_dir)
    elif file_type == 'images':
        results = carve_images_from_file(input_file, output_dir)
    else:
        carver = FileCarver(output_dir)
        try:
            ft = FileType(file_type)
            results = carver.carve_file(input_file, file_types=[ft])
        except ValueError:
            print(f"Unknown file type: {file_type}")
            sys.exit(1)

    print(f"\nCarving complete. Found {len(results)} files:")
    for r in results:
        print(f"  {r.file_type.value}: {r.output_path} ({r.size:,} bytes)")
