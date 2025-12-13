"""
Secure Storage Manager
Handles encrypted local storage for sensitive data in the PWA.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
import datetime
import hashlib
import base64
import json


class EncryptionAlgorithm(str, Enum):
    """Encryption algorithms for secure storage."""
    AES_GCM_256 = "AES-GCM-256"
    AES_CBC_256 = "AES-CBC-256"
    CHACHA20_POLY1305 = "ChaCha20-Poly1305"


class StorageType(str, Enum):
    """Types of storage backends."""
    INDEXED_DB = "indexeddb"
    LOCAL_STORAGE = "localstorage"
    SESSION_STORAGE = "sessionstorage"
    SECURE_ENCLAVE = "secure_enclave"  # iOS/Android native
    MEMORY = "memory"  # In-memory only


class SensitivityLevel(str, Enum):
    """Sensitivity levels for stored data."""
    PUBLIC = "public"  # No encryption
    INTERNAL = "internal"  # Basic encryption
    CONFIDENTIAL = "confidential"  # Strong encryption
    RESTRICTED = "restricted"  # Strong encryption + additional controls


@dataclass
class EncryptionKey:
    """An encryption key."""
    key_id: str
    algorithm: EncryptionAlgorithm
    key_hash: str  # Hash of the key for verification (never store actual key)
    created_at: str
    expires_at: Optional[str]
    is_active: bool
    purpose: str  # data, session, backup, etc.
    derived_from: Optional[str]  # Parent key ID if derived


@dataclass
class StorageEncryption:
    """Encryption configuration for storage."""
    enabled: bool
    algorithm: EncryptionAlgorithm
    key_derivation: str  # PBKDF2, Argon2, etc.
    iterations: int
    salt_length: int
    iv_length: int
    tag_length: int  # For GCM


@dataclass
class SecureItem:
    """A securely stored item."""
    item_id: str
    key: str  # Storage key
    encrypted_value: str  # Base64 encoded
    iv: str  # Initialization vector
    auth_tag: Optional[str]  # For GCM
    encryption_key_id: str

    # Metadata (unencrypted)
    sensitivity_level: SensitivityLevel
    storage_type: StorageType
    content_type: str  # json, string, binary
    original_size: int
    encrypted_size: int

    # Access control
    owner_id: str
    requires_biometric: bool
    requires_pin: bool
    access_count: int
    last_accessed: Optional[str]

    # Lifecycle
    created_at: str
    updated_at: str
    expires_at: Optional[str]
    auto_delete_after_access: bool


@dataclass
class StorageQuota:
    """Storage quota and usage."""
    total_bytes: int
    used_bytes: int
    available_bytes: int
    secure_storage_bytes: int
    cache_bytes: int
    evidence_bytes: int
    quota_percent_used: float


@dataclass
class StorageAuditEntry:
    """Audit log entry for storage operations."""
    audit_id: str
    item_id: str
    operation: str  # read, write, delete, export
    performed_by: str
    performed_at: str
    success: bool
    error_message: Optional[str]
    ip_address: Optional[str]
    device_id: Optional[str]


class SecureStorageManager:
    """Manages secure local storage for the PWA."""

    # Default encryption settings
    DEFAULT_ENCRYPTION = StorageEncryption(
        enabled=True,
        algorithm=EncryptionAlgorithm.AES_GCM_256,
        key_derivation="PBKDF2",
        iterations=100000,
        salt_length=16,
        iv_length=12,
        tag_length=16
    )

    # Storage prefixes
    PREFIXES = {
        SensitivityLevel.PUBLIC: "pub_",
        SensitivityLevel.INTERNAL: "int_",
        SensitivityLevel.CONFIDENTIAL: "conf_",
        SensitivityLevel.RESTRICTED: "rest_"
    }

    # Auto-expire times by sensitivity
    AUTO_EXPIRE = {
        SensitivityLevel.PUBLIC: None,  # Never
        SensitivityLevel.INTERNAL: 30 * 24 * 3600,  # 30 days
        SensitivityLevel.CONFIDENTIAL: 7 * 24 * 3600,  # 7 days
        SensitivityLevel.RESTRICTED: 24 * 3600  # 24 hours
    }

    def __init__(self, encryption_config: Optional[StorageEncryption] = None):
        self.encryption = encryption_config or self.DEFAULT_ENCRYPTION
        self.items: Dict[str, SecureItem] = {}
        self.keys: Dict[str, EncryptionKey] = {}
        self.audit_log: List[StorageAuditEntry] = []

    def create_encryption_key(
        self,
        purpose: str,
        algorithm: Optional[EncryptionAlgorithm] = None,
        expires_in_days: Optional[int] = None
    ) -> EncryptionKey:
        """Create a new encryption key."""
        key_id = hashlib.sha256(
            f"key-{purpose}-{datetime.datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]

        now = datetime.datetime.now()
        expires_at = None
        if expires_in_days:
            expires_at = (now + datetime.timedelta(days=expires_in_days)).isoformat()

        # In production, actual key would be generated using Web Crypto API
        # Here we just track metadata
        key_hash = hashlib.sha256(key_id.encode()).hexdigest()

        key = EncryptionKey(
            key_id=key_id,
            algorithm=algorithm or self.encryption.algorithm,
            key_hash=key_hash,
            created_at=now.isoformat(),
            expires_at=expires_at,
            is_active=True,
            purpose=purpose,
            derived_from=None
        )

        self.keys[key_id] = key
        return key

    def derive_key(
        self,
        parent_key_id: str,
        purpose: str,
        context: str
    ) -> Optional[EncryptionKey]:
        """Derive a new key from an existing key."""
        if parent_key_id not in self.keys:
            return None

        parent_key = self.keys[parent_key_id]
        if not parent_key.is_active:
            return None

        key_id = hashlib.sha256(
            f"derived-{parent_key_id}-{purpose}-{context}".encode()
        ).hexdigest()[:16]

        derived_key = EncryptionKey(
            key_id=key_id,
            algorithm=parent_key.algorithm,
            key_hash=hashlib.sha256(f"{parent_key.key_hash}-{context}".encode()).hexdigest(),
            created_at=datetime.datetime.now().isoformat(),
            expires_at=parent_key.expires_at,  # Inherit expiration
            is_active=True,
            purpose=purpose,
            derived_from=parent_key_id
        )

        self.keys[key_id] = derived_key
        return derived_key

    def store_secure(
        self,
        key: str,
        value: Any,
        owner_id: str,
        sensitivity_level: SensitivityLevel = SensitivityLevel.CONFIDENTIAL,
        storage_type: StorageType = StorageType.INDEXED_DB,
        encryption_key_id: Optional[str] = None,
        requires_biometric: bool = False,
        requires_pin: bool = False,
        expires_in_seconds: Optional[int] = None,
        auto_delete_after_access: bool = False,
        device_id: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> SecureItem:
        """Store data securely."""
        item_id = hashlib.sha256(
            f"item-{key}-{owner_id}-{datetime.datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]

        # Serialize value
        if isinstance(value, (dict, list)):
            serialized = json.dumps(value)
            content_type = "json"
        elif isinstance(value, bytes):
            serialized = base64.b64encode(value).decode()
            content_type = "binary"
        else:
            serialized = str(value)
            content_type = "string"

        original_size = len(serialized.encode())

        # Get or create encryption key
        if encryption_key_id is None:
            enc_key = self.create_encryption_key(f"item-{item_id}")
            encryption_key_id = enc_key.key_id

        # Simulate encryption (in production, use Web Crypto API)
        iv = base64.b64encode(
            hashlib.sha256(f"iv-{item_id}".encode()).digest()[:self.encryption.iv_length]
        ).decode()

        # Simulated encrypted value (in production, actual AES-GCM encryption)
        encrypted_value = base64.b64encode(
            serialized.encode()  # This would be actual ciphertext
        ).decode()

        auth_tag = base64.b64encode(
            hashlib.sha256(serialized.encode()).digest()[:self.encryption.tag_length]
        ).decode()

        # Calculate expiration
        now = datetime.datetime.now()
        if expires_in_seconds:
            expires_at = (now + datetime.timedelta(seconds=expires_in_seconds)).isoformat()
        elif self.AUTO_EXPIRE.get(sensitivity_level):
            expires_at = (now + datetime.timedelta(seconds=self.AUTO_EXPIRE[sensitivity_level])).isoformat()
        else:
            expires_at = None

        item = SecureItem(
            item_id=item_id,
            key=f"{self.PREFIXES[sensitivity_level]}{key}",
            encrypted_value=encrypted_value,
            iv=iv,
            auth_tag=auth_tag,
            encryption_key_id=encryption_key_id,
            sensitivity_level=sensitivity_level,
            storage_type=storage_type,
            content_type=content_type,
            original_size=original_size,
            encrypted_size=len(encrypted_value),
            owner_id=owner_id,
            requires_biometric=requires_biometric,
            requires_pin=requires_pin,
            access_count=0,
            last_accessed=None,
            created_at=now.isoformat(),
            updated_at=now.isoformat(),
            expires_at=expires_at,
            auto_delete_after_access=auto_delete_after_access
        )

        self.items[item_id] = item

        # Audit log
        self._log_audit(
            item_id=item_id,
            operation="write",
            performed_by=owner_id,
            success=True,
            device_id=device_id,
            ip_address=ip_address
        )

        return item

    def retrieve_secure(
        self,
        item_id: str,
        requester_id: str,
        biometric_verified: bool = False,
        pin_verified: bool = False,
        device_id: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Retrieve securely stored data."""
        if item_id not in self.items:
            self._log_audit(
                item_id=item_id,
                operation="read",
                performed_by=requester_id,
                success=False,
                error_message="Item not found",
                device_id=device_id,
                ip_address=ip_address
            )
            return None

        item = self.items[item_id]

        # Check ownership
        if item.owner_id != requester_id:
            self._log_audit(
                item_id=item_id,
                operation="read",
                performed_by=requester_id,
                success=False,
                error_message="Access denied - not owner",
                device_id=device_id,
                ip_address=ip_address
            )
            return None

        # Check expiration
        if item.expires_at:
            expires = datetime.datetime.fromisoformat(item.expires_at)
            if datetime.datetime.now() > expires:
                self._log_audit(
                    item_id=item_id,
                    operation="read",
                    performed_by=requester_id,
                    success=False,
                    error_message="Item expired",
                    device_id=device_id,
                    ip_address=ip_address
                )
                return None

        # Check biometric requirement
        if item.requires_biometric and not biometric_verified:
            self._log_audit(
                item_id=item_id,
                operation="read",
                performed_by=requester_id,
                success=False,
                error_message="Biometric verification required",
                device_id=device_id,
                ip_address=ip_address
            )
            return None

        # Check PIN requirement
        if item.requires_pin and not pin_verified:
            self._log_audit(
                item_id=item_id,
                operation="read",
                performed_by=requester_id,
                success=False,
                error_message="PIN verification required",
                device_id=device_id,
                ip_address=ip_address
            )
            return None

        # Decrypt (simulated - in production, use Web Crypto API)
        decrypted = base64.b64decode(item.encrypted_value).decode()

        # Deserialize
        if item.content_type == "json":
            value = json.loads(decrypted)
        elif item.content_type == "binary":
            value = base64.b64decode(decrypted)
        else:
            value = decrypted

        # Update access info
        item.access_count += 1
        item.last_accessed = datetime.datetime.now().isoformat()

        # Auto-delete if configured
        if item.auto_delete_after_access:
            del self.items[item_id]

        self._log_audit(
            item_id=item_id,
            operation="read",
            performed_by=requester_id,
            success=True,
            device_id=device_id,
            ip_address=ip_address
        )

        return {
            "item_id": item_id,
            "value": value,
            "content_type": item.content_type,
            "sensitivity_level": item.sensitivity_level.value,
            "access_count": item.access_count
        }

    def delete_secure(
        self,
        item_id: str,
        requester_id: str,
        device_id: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> bool:
        """Delete securely stored data."""
        if item_id not in self.items:
            self._log_audit(
                item_id=item_id,
                operation="delete",
                performed_by=requester_id,
                success=False,
                error_message="Item not found",
                device_id=device_id,
                ip_address=ip_address
            )
            return False

        item = self.items[item_id]

        # Check ownership
        if item.owner_id != requester_id:
            self._log_audit(
                item_id=item_id,
                operation="delete",
                performed_by=requester_id,
                success=False,
                error_message="Access denied - not owner",
                device_id=device_id,
                ip_address=ip_address
            )
            return False

        del self.items[item_id]

        self._log_audit(
            item_id=item_id,
            operation="delete",
            performed_by=requester_id,
            success=True,
            device_id=device_id,
            ip_address=ip_address
        )

        return True

    def update_secure(
        self,
        item_id: str,
        new_value: Any,
        requester_id: str,
        device_id: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> Optional[SecureItem]:
        """Update securely stored data."""
        if item_id not in self.items:
            return None

        item = self.items[item_id]

        # Check ownership
        if item.owner_id != requester_id:
            return None

        # Re-encrypt with new value
        if isinstance(new_value, (dict, list)):
            serialized = json.dumps(new_value)
            content_type = "json"
        elif isinstance(new_value, bytes):
            serialized = base64.b64encode(new_value).decode()
            content_type = "binary"
        else:
            serialized = str(new_value)
            content_type = "string"

        # Update encryption
        item.encrypted_value = base64.b64encode(serialized.encode()).decode()
        item.content_type = content_type
        item.original_size = len(serialized.encode())
        item.encrypted_size = len(item.encrypted_value)
        item.updated_at = datetime.datetime.now().isoformat()

        self._log_audit(
            item_id=item_id,
            operation="write",
            performed_by=requester_id,
            success=True,
            device_id=device_id,
            ip_address=ip_address
        )

        return item

    def list_items(
        self,
        owner_id: str,
        sensitivity_level: Optional[SensitivityLevel] = None,
        include_expired: bool = False
    ) -> List[Dict[str, Any]]:
        """List stored items for a user."""
        results = []
        now = datetime.datetime.now()

        for item in self.items.values():
            if item.owner_id != owner_id:
                continue

            if sensitivity_level and item.sensitivity_level != sensitivity_level:
                continue

            # Check expiration
            if not include_expired and item.expires_at:
                expires = datetime.datetime.fromisoformat(item.expires_at)
                if now > expires:
                    continue

            results.append({
                "item_id": item.item_id,
                "key": item.key,
                "sensitivity_level": item.sensitivity_level.value,
                "storage_type": item.storage_type.value,
                "content_type": item.content_type,
                "original_size": item.original_size,
                "requires_biometric": item.requires_biometric,
                "requires_pin": item.requires_pin,
                "created_at": item.created_at,
                "expires_at": item.expires_at,
                "access_count": item.access_count
            })

        return results

    def cleanup_expired(self) -> int:
        """Remove expired items."""
        now = datetime.datetime.now()
        expired_ids = []

        for item_id, item in self.items.items():
            if item.expires_at:
                expires = datetime.datetime.fromisoformat(item.expires_at)
                if now > expires:
                    expired_ids.append(item_id)

        for item_id in expired_ids:
            del self.items[item_id]
            self._log_audit(
                item_id=item_id,
                operation="delete",
                performed_by="system",
                success=True
            )

        return len(expired_ids)

    def rotate_encryption_key(
        self,
        old_key_id: str,
        new_key_id: str,
        owner_id: str
    ) -> Dict[str, Any]:
        """Rotate encryption key for all items."""
        results = {
            "rotated": 0,
            "failed": 0,
            "errors": []
        }

        if old_key_id not in self.keys or new_key_id not in self.keys:
            return {"error": "Invalid key ID"}

        for item in self.items.values():
            if item.encryption_key_id == old_key_id and item.owner_id == owner_id:
                try:
                    # In production: decrypt with old key, re-encrypt with new key
                    item.encryption_key_id = new_key_id
                    item.updated_at = datetime.datetime.now().isoformat()
                    results["rotated"] += 1
                except Exception as e:
                    results["failed"] += 1
                    results["errors"].append(str(e))

        # Deactivate old key
        self.keys[old_key_id].is_active = False

        return results

    def get_storage_quota(self, owner_id: str) -> StorageQuota:
        """Get storage quota and usage for a user."""
        # Simulated quota (in production, query actual storage)
        total = 100 * 1024 * 1024  # 100 MB

        user_items = [i for i in self.items.values() if i.owner_id == owner_id]
        used = sum(item.encrypted_size for item in user_items)

        secure_storage = sum(
            item.encrypted_size for item in user_items
            if item.sensitivity_level in [SensitivityLevel.CONFIDENTIAL, SensitivityLevel.RESTRICTED]
        )

        cache = sum(
            item.encrypted_size for item in user_items
            if item.sensitivity_level == SensitivityLevel.PUBLIC
        )

        return StorageQuota(
            total_bytes=total,
            used_bytes=used,
            available_bytes=total - used,
            secure_storage_bytes=secure_storage,
            cache_bytes=cache,
            evidence_bytes=0,  # Would query evidence storage
            quota_percent_used=round(used / total * 100, 2)
        )

    def export_for_backup(
        self,
        owner_id: str,
        backup_key_id: str
    ) -> Optional[Dict[str, Any]]:
        """Export encrypted data for backup."""
        if backup_key_id not in self.keys:
            return None

        items_to_export = [
            {
                "item_id": item.item_id,
                "key": item.key,
                "encrypted_value": item.encrypted_value,
                "iv": item.iv,
                "auth_tag": item.auth_tag,
                "sensitivity_level": item.sensitivity_level.value,
                "content_type": item.content_type,
                "created_at": item.created_at
            }
            for item in self.items.values()
            if item.owner_id == owner_id
        ]

        # In production, re-encrypt with backup key
        backup_data = {
            "version": "1.0",
            "exported_at": datetime.datetime.now().isoformat(),
            "owner_id": owner_id,
            "backup_key_id": backup_key_id,
            "item_count": len(items_to_export),
            "items": items_to_export
        }

        self._log_audit(
            item_id="backup",
            operation="export",
            performed_by=owner_id,
            success=True
        )

        return backup_data

    def get_audit_log(
        self,
        item_id: Optional[str] = None,
        owner_id: Optional[str] = None,
        operation: Optional[str] = None,
        limit: int = 100
    ) -> List[StorageAuditEntry]:
        """Get audit log entries."""
        entries = self.audit_log.copy()

        if item_id:
            entries = [e for e in entries if e.item_id == item_id]
        if operation:
            entries = [e for e in entries if e.operation == operation]

        # Sort by timestamp descending
        entries.sort(key=lambda e: e.performed_at, reverse=True)

        return entries[:limit]

    def _log_audit(
        self,
        item_id: str,
        operation: str,
        performed_by: str,
        success: bool,
        error_message: Optional[str] = None,
        device_id: Optional[str] = None,
        ip_address: Optional[str] = None
    ):
        """Add an audit log entry."""
        audit_id = hashlib.sha256(
            f"audit-{item_id}-{operation}-{datetime.datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]

        entry = StorageAuditEntry(
            audit_id=audit_id,
            item_id=item_id,
            operation=operation,
            performed_by=performed_by,
            performed_at=datetime.datetime.now().isoformat(),
            success=success,
            error_message=error_message,
            ip_address=ip_address,
            device_id=device_id
        )

        self.audit_log.append(entry)

        # Keep only last 10000 entries
        if len(self.audit_log) > 10000:
            self.audit_log = self.audit_log[-10000:]

    def get_statistics(self) -> Dict[str, Any]:
        """Get secure storage statistics."""
        total_items = len(self.items)
        total_keys = len(self.keys)
        active_keys = sum(1 for k in self.keys.values() if k.is_active)

        by_sensitivity = {}
        by_storage = {}
        total_size = 0

        for item in self.items.values():
            sl = item.sensitivity_level.value
            by_sensitivity[sl] = by_sensitivity.get(sl, 0) + 1

            st = item.storage_type.value
            by_storage[st] = by_storage.get(st, 0) + 1

            total_size += item.encrypted_size

        return {
            "total_items": total_items,
            "total_encryption_keys": total_keys,
            "active_encryption_keys": active_keys,
            "total_encrypted_size_bytes": total_size,
            "total_encrypted_size_mb": round(total_size / (1024 * 1024), 2),
            "by_sensitivity_level": by_sensitivity,
            "by_storage_type": by_storage,
            "audit_log_entries": len(self.audit_log)
        }
