"""
Offline Manager
Handles offline functionality, caching, and synchronization for PWA.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Callable
from enum import Enum
import datetime
import hashlib
import json


class CacheStrategy(str, Enum):
    """Caching strategies for different content types."""
    CACHE_FIRST = "cache_first"  # Try cache, fallback to network
    NETWORK_FIRST = "network_first"  # Try network, fallback to cache
    CACHE_ONLY = "cache_only"  # Only use cache
    NETWORK_ONLY = "network_only"  # Only use network
    STALE_WHILE_REVALIDATE = "stale_while_revalidate"  # Return cache, update in background


class ConflictResolution(str, Enum):
    """Strategies for resolving sync conflicts."""
    SERVER_WINS = "server_wins"
    CLIENT_WINS = "client_wins"
    NEWEST_WINS = "newest_wins"
    MERGE = "merge"
    MANUAL = "manual"


@dataclass
class CacheEntry:
    """A cached item."""
    cache_key: str
    url: str
    response_data: bytes
    content_type: str
    etag: Optional[str]
    last_modified: Optional[str]

    # Cache metadata
    cached_at: str
    expires_at: Optional[str]
    max_age_seconds: Optional[int]

    # Size and integrity
    size_bytes: int
    content_hash: str

    # Strategy
    strategy: CacheStrategy
    is_valid: bool = True


@dataclass
class SyncItem:
    """An item pending synchronization."""
    sync_id: str
    item_type: str  # evidence, note, document, etc.
    item_id: str
    action: str  # create, update, delete
    data: Dict[str, Any]

    # Timestamps
    created_at: str
    modified_at: str

    # Sync status
    attempts: int = 0
    last_attempt: Optional[str] = None
    last_error: Optional[str] = None
    is_synced: bool = False
    synced_at: Optional[str] = None

    # Conflict handling
    has_conflict: bool = False
    server_version: Optional[Dict[str, Any]] = None


@dataclass
class SyncConflict:
    """A synchronization conflict."""
    conflict_id: str
    sync_item: SyncItem
    local_data: Dict[str, Any]
    server_data: Dict[str, Any]
    local_modified: str
    server_modified: str
    resolution: Optional[ConflictResolution] = None
    resolved_data: Optional[Dict[str, Any]] = None
    resolved_at: Optional[str] = None
    resolved_by: Optional[str] = None


@dataclass
class SyncStatus:
    """Overall synchronization status."""
    is_online: bool
    last_sync: Optional[str]
    pending_items: int
    failed_items: int
    conflicts: int
    sync_in_progress: bool
    next_sync_scheduled: Optional[str]


class OfflineManager:
    """Manages offline functionality and synchronization."""

    # Cache size limits (in bytes)
    MAX_CACHE_SIZE = 500 * 1024 * 1024  # 500 MB
    MAX_ITEM_SIZE = 50 * 1024 * 1024  # 50 MB per item

    # Default cache strategies by content type
    DEFAULT_STRATEGIES = {
        "text/html": CacheStrategy.NETWORK_FIRST,
        "application/json": CacheStrategy.NETWORK_FIRST,
        "image/*": CacheStrategy.CACHE_FIRST,
        "video/*": CacheStrategy.CACHE_FIRST,
        "audio/*": CacheStrategy.CACHE_FIRST,
        "application/pdf": CacheStrategy.CACHE_FIRST,
        "font/*": CacheStrategy.CACHE_FIRST,
        "text/css": CacheStrategy.STALE_WHILE_REVALIDATE,
        "application/javascript": CacheStrategy.STALE_WHILE_REVALIDATE,
    }

    # Critical paths that must be available offline
    CRITICAL_PATHS = [
        "/",
        "/dashboard",
        "/evidence",
        "/emergency",
        "/contacts",
        "/offline.html",
        "/manifest.json",
        "/service-worker.js"
    ]

    def __init__(self):
        self.cache: Dict[str, CacheEntry] = {}
        self.sync_queue: Dict[str, SyncItem] = {}
        self.conflicts: Dict[str, SyncConflict] = {}
        self.is_online = True
        self.sync_in_progress = False
        self.last_sync: Optional[str] = None

    def cache_response(
        self,
        url: str,
        response_data: bytes,
        content_type: str,
        strategy: Optional[CacheStrategy] = None,
        max_age_seconds: Optional[int] = None,
        etag: Optional[str] = None,
        last_modified: Optional[str] = None
    ) -> CacheEntry:
        """Cache a response."""
        if len(response_data) > self.MAX_ITEM_SIZE:
            raise ValueError(f"Response too large to cache: {len(response_data)} bytes")

        # Determine strategy
        if strategy is None:
            strategy = self._get_strategy_for_content_type(content_type)

        cache_key = self._generate_cache_key(url)
        now = datetime.datetime.now()

        # Calculate expiration
        expires_at = None
        if max_age_seconds:
            expires_at = (now + datetime.timedelta(seconds=max_age_seconds)).isoformat()

        entry = CacheEntry(
            cache_key=cache_key,
            url=url,
            response_data=response_data,
            content_type=content_type,
            etag=etag,
            last_modified=last_modified,
            cached_at=now.isoformat(),
            expires_at=expires_at,
            max_age_seconds=max_age_seconds,
            size_bytes=len(response_data),
            content_hash=hashlib.sha256(response_data).hexdigest(),
            strategy=strategy,
            is_valid=True
        )

        # Check cache size limit
        self._ensure_cache_space(len(response_data))

        self.cache[cache_key] = entry
        return entry

    def get_cached(self, url: str) -> Optional[CacheEntry]:
        """Get a cached response."""
        cache_key = self._generate_cache_key(url)
        entry = self.cache.get(cache_key)

        if entry is None:
            return None

        # Check if expired
        if entry.expires_at:
            expires = datetime.datetime.fromisoformat(entry.expires_at)
            if datetime.datetime.now() > expires:
                entry.is_valid = False

        return entry

    def invalidate_cache(self, url: str) -> bool:
        """Invalidate a cached item."""
        cache_key = self._generate_cache_key(url)
        if cache_key in self.cache:
            del self.cache[cache_key]
            return True
        return False

    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate cache entries matching a pattern."""
        count = 0
        keys_to_remove = []

        for key, entry in self.cache.items():
            if pattern in entry.url:
                keys_to_remove.append(key)
                count += 1

        for key in keys_to_remove:
            del self.cache[key]

        return count

    def queue_sync(
        self,
        item_type: str,
        item_id: str,
        action: str,
        data: Dict[str, Any]
    ) -> SyncItem:
        """Queue an item for synchronization."""
        sync_id = hashlib.md5(
            f"{item_type}-{item_id}-{action}-{datetime.datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]

        now = datetime.datetime.now().isoformat()

        sync_item = SyncItem(
            sync_id=sync_id,
            item_type=item_type,
            item_id=item_id,
            action=action,
            data=data,
            created_at=now,
            modified_at=now,
            attempts=0
        )

        self.sync_queue[sync_id] = sync_item
        return sync_item

    def process_sync_queue(
        self,
        sync_handler: Callable[[SyncItem], Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Process pending sync items."""
        if self.sync_in_progress:
            return {"status": "already_running"}

        if not self.is_online:
            return {"status": "offline", "pending": len(self.sync_queue)}

        self.sync_in_progress = True
        results = {
            "synced": 0,
            "failed": 0,
            "conflicts": 0,
            "errors": []
        }

        try:
            # Sort by creation time
            sorted_items = sorted(
                self.sync_queue.values(),
                key=lambda x: x.created_at
            )

            for item in sorted_items:
                if item.is_synced:
                    continue

                item.attempts += 1
                item.last_attempt = datetime.datetime.now().isoformat()

                try:
                    result = sync_handler(item)

                    if result.get("success"):
                        item.is_synced = True
                        item.synced_at = datetime.datetime.now().isoformat()
                        results["synced"] += 1

                    elif result.get("conflict"):
                        self._create_conflict(item, result.get("server_data", {}))
                        results["conflicts"] += 1

                    else:
                        item.last_error = result.get("error", "Unknown error")
                        results["failed"] += 1
                        results["errors"].append({
                            "sync_id": item.sync_id,
                            "error": item.last_error
                        })

                except Exception as e:
                    item.last_error = str(e)
                    results["failed"] += 1
                    results["errors"].append({
                        "sync_id": item.sync_id,
                        "error": str(e)
                    })

            self.last_sync = datetime.datetime.now().isoformat()

        finally:
            self.sync_in_progress = False

        return results

    def resolve_conflict(
        self,
        conflict_id: str,
        resolution: ConflictResolution,
        resolved_by: str,
        merged_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Resolve a sync conflict."""
        if conflict_id not in self.conflicts:
            return False

        conflict = self.conflicts[conflict_id]
        now = datetime.datetime.now().isoformat()

        conflict.resolution = resolution
        conflict.resolved_at = now
        conflict.resolved_by = resolved_by

        # Determine final data based on resolution
        if resolution == ConflictResolution.SERVER_WINS:
            conflict.resolved_data = conflict.server_data
        elif resolution == ConflictResolution.CLIENT_WINS:
            conflict.resolved_data = conflict.local_data
        elif resolution == ConflictResolution.NEWEST_WINS:
            if conflict.local_modified > conflict.server_modified:
                conflict.resolved_data = conflict.local_data
            else:
                conflict.resolved_data = conflict.server_data
        elif resolution == ConflictResolution.MERGE:
            if merged_data is None:
                return False
            conflict.resolved_data = merged_data
        elif resolution == ConflictResolution.MANUAL:
            if merged_data is None:
                return False
            conflict.resolved_data = merged_data

        # Update sync item
        conflict.sync_item.data = conflict.resolved_data
        conflict.sync_item.has_conflict = False
        conflict.sync_item.is_synced = False  # Re-queue for sync

        return True

    def _create_conflict(self, item: SyncItem, server_data: Dict[str, Any]):
        """Create a sync conflict."""
        conflict_id = hashlib.md5(
            f"conflict-{item.sync_id}-{datetime.datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]

        conflict = SyncConflict(
            conflict_id=conflict_id,
            sync_item=item,
            local_data=item.data.copy(),
            server_data=server_data,
            local_modified=item.modified_at,
            server_modified=server_data.get("modified_at", datetime.datetime.now().isoformat())
        )

        item.has_conflict = True
        item.server_version = server_data

        self.conflicts[conflict_id] = conflict

    def get_sync_status(self) -> SyncStatus:
        """Get current synchronization status."""
        pending = sum(1 for item in self.sync_queue.values() if not item.is_synced)
        failed = sum(1 for item in self.sync_queue.values()
                     if item.attempts > 0 and not item.is_synced and not item.has_conflict)

        return SyncStatus(
            is_online=self.is_online,
            last_sync=self.last_sync,
            pending_items=pending,
            failed_items=failed,
            conflicts=len(self.conflicts),
            sync_in_progress=self.sync_in_progress,
            next_sync_scheduled=None
        )

    def set_online_status(self, is_online: bool):
        """Update online status."""
        self.is_online = is_online

    def precache_critical_paths(self, fetch_handler: Callable[[str], bytes]) -> Dict[str, Any]:
        """Pre-cache critical paths for offline access."""
        results = {
            "cached": [],
            "failed": []
        }

        for path in self.CRITICAL_PATHS:
            try:
                data = fetch_handler(path)
                self.cache_response(
                    url=path,
                    response_data=data,
                    content_type="text/html",
                    strategy=CacheStrategy.CACHE_FIRST,
                    max_age_seconds=86400 * 7  # 7 days
                )
                results["cached"].append(path)
            except Exception as e:
                results["failed"].append({"path": path, "error": str(e)})

        return results

    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_size = sum(entry.size_bytes for entry in self.cache.values())
        valid_entries = sum(1 for entry in self.cache.values() if entry.is_valid)

        by_type = {}
        for entry in self.cache.values():
            content_type = entry.content_type.split(";")[0]
            if content_type not in by_type:
                by_type[content_type] = {"count": 0, "size": 0}
            by_type[content_type]["count"] += 1
            by_type[content_type]["size"] += entry.size_bytes

        return {
            "total_entries": len(self.cache),
            "valid_entries": valid_entries,
            "expired_entries": len(self.cache) - valid_entries,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "max_size_mb": self.MAX_CACHE_SIZE / (1024 * 1024),
            "usage_percent": round(total_size / self.MAX_CACHE_SIZE * 100, 2),
            "by_content_type": by_type
        }

    def clear_cache(self, expired_only: bool = False) -> int:
        """Clear cache."""
        if expired_only:
            keys_to_remove = [
                key for key, entry in self.cache.items()
                if not entry.is_valid
            ]
            for key in keys_to_remove:
                del self.cache[key]
            return len(keys_to_remove)
        else:
            count = len(self.cache)
            self.cache.clear()
            return count

    def _generate_cache_key(self, url: str) -> str:
        """Generate a cache key for a URL."""
        return hashlib.sha256(url.encode()).hexdigest()[:24]

    def _get_strategy_for_content_type(self, content_type: str) -> CacheStrategy:
        """Get the default caching strategy for a content type."""
        base_type = content_type.split(";")[0].strip()

        # Check exact match
        if base_type in self.DEFAULT_STRATEGIES:
            return self.DEFAULT_STRATEGIES[base_type]

        # Check wildcard match (e.g., image/*)
        type_prefix = base_type.split("/")[0] + "/*"
        if type_prefix in self.DEFAULT_STRATEGIES:
            return self.DEFAULT_STRATEGIES[type_prefix]

        # Default strategy
        return CacheStrategy.NETWORK_FIRST

    def _ensure_cache_space(self, needed_bytes: int):
        """Ensure there's enough cache space, evicting if necessary."""
        current_size = sum(entry.size_bytes for entry in self.cache.values())

        if current_size + needed_bytes <= self.MAX_CACHE_SIZE:
            return

        # Need to evict - use LRU strategy
        sorted_entries = sorted(
            self.cache.items(),
            key=lambda x: x[1].cached_at
        )

        bytes_to_free = (current_size + needed_bytes) - self.MAX_CACHE_SIZE
        freed = 0

        for key, entry in sorted_entries:
            if freed >= bytes_to_free:
                break
            freed += entry.size_bytes
            del self.cache[key]

    def export_offline_data(self) -> Dict[str, Any]:
        """Export offline data for backup."""
        return {
            "exported_at": datetime.datetime.now().isoformat(),
            "sync_queue": [
                {
                    "sync_id": item.sync_id,
                    "item_type": item.item_type,
                    "item_id": item.item_id,
                    "action": item.action,
                    "data": item.data,
                    "created_at": item.created_at,
                    "is_synced": item.is_synced
                }
                for item in self.sync_queue.values()
                if not item.is_synced
            ],
            "conflicts": [
                {
                    "conflict_id": c.conflict_id,
                    "local_data": c.local_data,
                    "server_data": c.server_data,
                    "local_modified": c.local_modified,
                    "server_modified": c.server_modified
                }
                for c in self.conflicts.values()
            ],
            "cache_stats": self.get_cache_statistics()
        }

    def import_offline_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Import offline data from backup."""
        results = {
            "sync_items_imported": 0,
            "conflicts_imported": 0,
            "errors": []
        }

        for item_data in data.get("sync_queue", []):
            try:
                item = SyncItem(
                    sync_id=item_data["sync_id"],
                    item_type=item_data["item_type"],
                    item_id=item_data["item_id"],
                    action=item_data["action"],
                    data=item_data["data"],
                    created_at=item_data["created_at"],
                    modified_at=item_data["created_at"],
                    is_synced=item_data.get("is_synced", False)
                )
                self.sync_queue[item.sync_id] = item
                results["sync_items_imported"] += 1
            except Exception as e:
                results["errors"].append(str(e))

        return results
