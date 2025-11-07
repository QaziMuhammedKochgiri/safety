import os
import uuid
from datetime import datetime
from pathlib import Path

def generate_client_number():
    """Generate unique client number in format SC2025XXX"""
    year = datetime.now().year
    unique_id = str(uuid.uuid4().int)[:3].zfill(3)
    return f"SC{year}{unique_id}"

def generate_document_number():
    """Generate unique document number in format DOC2025XXX"""
    year = datetime.now().year
    unique_id = str(uuid.uuid4().int)[:3].zfill(3)
    return f"DOC{year}{unique_id}"

def get_upload_directory(client_number: str):
    """Get or create upload directory for a client"""
    upload_base = Path("/app/backend/uploads")
    client_dir = upload_base / client_number
    client_dir.mkdir(parents=True, exist_ok=True)
    return str(client_dir)

def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal"""
    # Remove any path components
    filename = os.path.basename(filename)
    # Remove any potentially dangerous characters
    safe_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-_")
    filename = ''.join(c if c in safe_chars else '_' for c in filename)
    return filename

def get_file_extension(filename: str) -> str:
    """Get file extension"""
    return Path(filename).suffix.lower()

def is_allowed_file_type(filename: str, allowed_types: list) -> bool:
    """Check if file type is allowed"""
    ext = get_file_extension(filename)
    return ext in allowed_types
