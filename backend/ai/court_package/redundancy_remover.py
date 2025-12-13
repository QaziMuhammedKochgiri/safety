"""
Redundancy Remover
Duplicate and near-duplicate detection for evidence packages.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Set, Tuple
from enum import Enum
from datetime import datetime
import hashlib
import re
from collections import defaultdict


class SimilarityType(str, Enum):
    """Types of similarity between evidence items."""
    EXACT_DUPLICATE = "exact_duplicate"  # Identical content
    NEAR_DUPLICATE = "near_duplicate"  # Very similar content
    SEMANTIC_DUPLICATE = "semantic_duplicate"  # Same meaning, different words
    TEMPORAL_DUPLICATE = "temporal_duplicate"  # Same event, different angles
    SUPERSEDED = "superseded"  # Older version of same document
    SUBSET = "subset"  # Content is part of another item
    OVERLAPPING = "overlapping"  # Partial content overlap


class RemovalAction(str, Enum):
    """Action to take for redundant items."""
    REMOVE = "remove"  # Remove completely
    MERGE = "merge"  # Merge with primary
    KEEP_REFERENCE = "keep_reference"  # Keep as reference only
    KEEP_ALL = "keep_all"  # Keep all versions


@dataclass
class DuplicateGroup:
    """A group of duplicate/similar items."""
    group_id: str
    similarity_type: SimilarityType
    primary_item_id: str  # The item to keep
    duplicate_item_ids: List[str]  # Items that are duplicates
    similarity_scores: Dict[str, float]  # item_id -> similarity score
    recommendation: RemovalAction
    explanation: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DeduplicationResult:
    """Result of deduplication process."""
    case_id: str
    original_count: int
    final_count: int
    removed_count: int
    duplicate_groups: List[DuplicateGroup]
    items_to_keep: List[str]
    items_to_remove: List[str]
    items_to_merge: List[Tuple[str, str]]  # (source, target)
    space_saved_bytes: int
    pages_saved: int
    processing_time_seconds: float
    created_at: datetime


class RedundancyRemover:
    """Detects and removes redundant evidence."""

    def __init__(self):
        self.content_hashes: Dict[str, str] = {}  # item_id -> content_hash
        self.content_index: Dict[str, List[str]] = {}  # hash -> item_ids
        self.similarity_cache: Dict[str, Dict[str, float]] = {}  # item_id -> {item_id: score}

    def analyze_redundancy(
        self,
        items: List[Dict[str, Any]],
        similarity_threshold: float = 0.85
    ) -> DeduplicationResult:
        """Analyze a collection of items for redundancy."""
        start_time = datetime.utcnow()

        # Build content index
        self._build_content_index(items)

        # Detect duplicate groups
        duplicate_groups: List[DuplicateGroup] = []

        # 1. Find exact duplicates
        exact_groups = self._find_exact_duplicates()
        duplicate_groups.extend(exact_groups)

        # 2. Find near duplicates
        near_groups = self._find_near_duplicates(items, similarity_threshold)
        duplicate_groups.extend(near_groups)

        # 3. Find temporal duplicates
        temporal_groups = self._find_temporal_duplicates(items)
        duplicate_groups.extend(temporal_groups)

        # 4. Find superseded documents
        superseded_groups = self._find_superseded_documents(items)
        duplicate_groups.extend(superseded_groups)

        # 5. Find subset relationships
        subset_groups = self._find_subsets(items)
        duplicate_groups.extend(subset_groups)

        # Determine items to keep/remove
        items_to_keep, items_to_remove, items_to_merge = self._determine_actions(
            items, duplicate_groups
        )

        # Calculate savings
        item_map = {i.get("item_id"): i for i in items}
        space_saved = sum(
            item_map.get(item_id, {}).get("file_size_bytes", 0)
            for item_id in items_to_remove
        )
        pages_saved = sum(
            item_map.get(item_id, {}).get("estimated_pages", 1)
            for item_id in items_to_remove
        )

        end_time = datetime.utcnow()

        return DeduplicationResult(
            case_id=items[0].get("case_id", "") if items else "",
            original_count=len(items),
            final_count=len(items_to_keep),
            removed_count=len(items_to_remove),
            duplicate_groups=duplicate_groups,
            items_to_keep=items_to_keep,
            items_to_remove=items_to_remove,
            items_to_merge=items_to_merge,
            space_saved_bytes=space_saved,
            pages_saved=pages_saved,
            processing_time_seconds=(end_time - start_time).total_seconds(),
            created_at=datetime.utcnow()
        )

    def _build_content_index(self, items: List[Dict[str, Any]]):
        """Build index of content hashes."""
        self.content_hashes.clear()
        self.content_index.clear()

        for item in items:
            item_id = item.get("item_id", "")
            content = item.get("content", "")

            # Generate hash
            content_hash = self._hash_content(content)
            self.content_hashes[item_id] = content_hash

            # Add to index
            if content_hash not in self.content_index:
                self.content_index[content_hash] = []
            self.content_index[content_hash].append(item_id)

    def _hash_content(self, content: str) -> str:
        """Generate hash for content."""
        normalized = self._normalize_content(content)
        return hashlib.sha256(normalized.encode()).hexdigest()

    def _normalize_content(self, content: str) -> str:
        """Normalize content for comparison."""
        if not content:
            return ""

        # Lowercase
        normalized = content.lower()

        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized).strip()

        # Remove common punctuation variations
        normalized = re.sub(r'[^\w\s]', '', normalized)

        return normalized

    def _find_exact_duplicates(self) -> List[DuplicateGroup]:
        """Find exactly duplicate items."""
        groups = []

        for content_hash, item_ids in self.content_index.items():
            if len(item_ids) > 1:
                # Choose primary (first one, or could use other criteria)
                primary = item_ids[0]
                duplicates = item_ids[1:]

                group = DuplicateGroup(
                    group_id=f"exact_{content_hash[:16]}",
                    similarity_type=SimilarityType.EXACT_DUPLICATE,
                    primary_item_id=primary,
                    duplicate_item_ids=duplicates,
                    similarity_scores={d: 1.0 for d in duplicates},
                    recommendation=RemovalAction.REMOVE,
                    explanation=f"Exact duplicate content ({len(duplicates)} copies)"
                )
                groups.append(group)

        return groups

    def _find_near_duplicates(
        self,
        items: List[Dict[str, Any]],
        threshold: float
    ) -> List[DuplicateGroup]:
        """Find near-duplicate items using similarity comparison."""
        groups = []
        processed: Set[str] = set()

        # Get exact duplicate IDs to skip
        exact_duplicates = set()
        for content_hash, item_ids in self.content_index.items():
            if len(item_ids) > 1:
                exact_duplicates.update(item_ids[1:])

        for i, item1 in enumerate(items):
            item1_id = item1.get("item_id", "")

            if item1_id in processed or item1_id in exact_duplicates:
                continue

            near_duplicates = []
            similarity_scores = {}

            for j, item2 in enumerate(items):
                if i >= j:
                    continue

                item2_id = item2.get("item_id", "")
                if item2_id in processed or item2_id in exact_duplicates:
                    continue

                # Compare content
                similarity = self._calculate_similarity(
                    item1.get("content", ""),
                    item2.get("content", "")
                )

                if similarity >= threshold and similarity < 1.0:
                    near_duplicates.append(item2_id)
                    similarity_scores[item2_id] = similarity
                    processed.add(item2_id)

            if near_duplicates:
                processed.add(item1_id)

                group = DuplicateGroup(
                    group_id=f"near_{item1_id[:16]}",
                    similarity_type=SimilarityType.NEAR_DUPLICATE,
                    primary_item_id=item1_id,
                    duplicate_item_ids=near_duplicates,
                    similarity_scores=similarity_scores,
                    recommendation=RemovalAction.KEEP_REFERENCE,
                    explanation=(
                        f"Near-duplicate content ({len(near_duplicates)} similar items, "
                        f"avg similarity: {sum(similarity_scores.values())/len(similarity_scores):.2%})"
                    )
                )
                groups.append(group)

        return groups

    def _calculate_similarity(self, content1: str, content2: str) -> float:
        """Calculate similarity between two content strings."""
        if not content1 or not content2:
            return 0.0

        # Use cached result if available
        cache_key = f"{hash(content1)}_{hash(content2)}"
        if content1 in self.similarity_cache:
            if content2 in self.similarity_cache[content1]:
                return self.similarity_cache[content1][content2]

        # Normalize
        norm1 = self._normalize_content(content1)
        norm2 = self._normalize_content(content2)

        # Jaccard similarity on word sets
        words1 = set(norm1.split())
        words2 = set(norm2.split())

        if not words1 or not words2:
            return 0.0

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        similarity = intersection / union if union > 0 else 0.0

        # Cache result
        if content1 not in self.similarity_cache:
            self.similarity_cache[content1] = {}
        self.similarity_cache[content1][content2] = similarity

        return similarity

    def _find_temporal_duplicates(
        self,
        items: List[Dict[str, Any]]
    ) -> List[DuplicateGroup]:
        """Find items that describe the same event at different times."""
        groups = []

        # Group items by date
        by_date: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

        for item in items:
            date_created = item.get("date_created")
            if isinstance(date_created, datetime):
                date_key = date_created.strftime("%Y-%m-%d")
            elif isinstance(date_created, str):
                date_key = date_created[:10]
            else:
                continue

            by_date[date_key].append(item)

        # Check for duplicates within same day
        for date_key, day_items in by_date.items():
            if len(day_items) < 2:
                continue

            # Look for items with similar participants and content
            processed: Set[str] = set()

            for i, item1 in enumerate(day_items):
                item1_id = item1.get("item_id", "")
                if item1_id in processed:
                    continue

                temporal_dups = []
                scores = {}

                for j, item2 in enumerate(day_items):
                    if i >= j:
                        continue

                    item2_id = item2.get("item_id", "")
                    if item2_id in processed:
                        continue

                    # Check participant overlap
                    p1 = set(item1.get("participants", []))
                    p2 = set(item2.get("participants", []))

                    if p1 and p2 and len(p1 & p2) > 0:
                        # Check content similarity
                        similarity = self._calculate_similarity(
                            item1.get("content", ""),
                            item2.get("content", "")
                        )

                        if similarity >= 0.5:
                            temporal_dups.append(item2_id)
                            scores[item2_id] = similarity
                            processed.add(item2_id)

                if temporal_dups:
                    processed.add(item1_id)

                    group = DuplicateGroup(
                        group_id=f"temporal_{date_key}_{item1_id[:8]}",
                        similarity_type=SimilarityType.TEMPORAL_DUPLICATE,
                        primary_item_id=item1_id,
                        duplicate_item_ids=temporal_dups,
                        similarity_scores=scores,
                        recommendation=RemovalAction.MERGE,
                        explanation=(
                            f"Same event on {date_key} from different perspectives"
                        )
                    )
                    groups.append(group)

        return groups

    def _find_superseded_documents(
        self,
        items: List[Dict[str, Any]]
    ) -> List[DuplicateGroup]:
        """Find documents that supersede older versions."""
        groups = []

        # Look for versioned documents
        document_types = ["court_order", "custody_agreement", "restraining_order"]

        doc_items = [
            item for item in items
            if item.get("evidence_type") in document_types
        ]

        # Group by document type and participants
        by_type_participants: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

        for item in doc_items:
            doc_type = item.get("evidence_type", "")
            participants = tuple(sorted(item.get("participants", [])))
            key = f"{doc_type}_{participants}"
            by_type_participants[key].append(item)

        for key, type_items in by_type_participants.items():
            if len(type_items) < 2:
                continue

            # Sort by date (newest first)
            sorted_items = sorted(
                type_items,
                key=lambda x: x.get("date_created", datetime.min),
                reverse=True
            )

            # Newest is primary, older are superseded
            primary = sorted_items[0]
            superseded = sorted_items[1:]

            if superseded:
                group = DuplicateGroup(
                    group_id=f"superseded_{key[:24]}",
                    similarity_type=SimilarityType.SUPERSEDED,
                    primary_item_id=primary.get("item_id", ""),
                    duplicate_item_ids=[s.get("item_id", "") for s in superseded],
                    similarity_scores={
                        s.get("item_id", ""): 0.5 for s in superseded
                    },
                    recommendation=RemovalAction.KEEP_REFERENCE,
                    explanation=(
                        f"Older versions of {primary.get('evidence_type', 'document')}"
                    ),
                    metadata={
                        "newest_date": primary.get("date_created"),
                        "oldest_date": superseded[-1].get("date_created")
                    }
                )
                groups.append(group)

        return groups

    def _find_subsets(
        self,
        items: List[Dict[str, Any]]
    ) -> List[DuplicateGroup]:
        """Find items that are subsets of larger items."""
        groups = []
        processed: Set[str] = set()

        # Sort by content length (longest first)
        sorted_items = sorted(
            items,
            key=lambda x: len(x.get("content", "")),
            reverse=True
        )

        for i, large_item in enumerate(sorted_items):
            large_id = large_item.get("item_id", "")
            large_content = self._normalize_content(large_item.get("content", ""))

            if not large_content or large_id in processed:
                continue

            subset_items = []
            scores = {}

            for j, small_item in enumerate(sorted_items):
                if i >= j:
                    continue

                small_id = small_item.get("item_id", "")
                small_content = self._normalize_content(small_item.get("content", ""))

                if not small_content or small_id in processed:
                    continue

                # Check if small is subset of large
                if len(small_content) < len(large_content) * 0.8:
                    # Check if small content is contained in large
                    small_words = set(small_content.split())
                    large_words = set(large_content.split())

                    if small_words and small_words.issubset(large_words):
                        coverage = len(small_words) / len(large_words)
                        if coverage < 0.8:  # Only if significantly smaller
                            subset_items.append(small_id)
                            scores[small_id] = coverage
                            processed.add(small_id)

            if subset_items:
                group = DuplicateGroup(
                    group_id=f"subset_{large_id[:16]}",
                    similarity_type=SimilarityType.SUBSET,
                    primary_item_id=large_id,
                    duplicate_item_ids=subset_items,
                    similarity_scores=scores,
                    recommendation=RemovalAction.REMOVE,
                    explanation=(
                        f"{len(subset_items)} items are contained within larger item"
                    )
                )
                groups.append(group)

        return groups

    def _determine_actions(
        self,
        items: List[Dict[str, Any]],
        groups: List[DuplicateGroup]
    ) -> Tuple[List[str], List[str], List[Tuple[str, str]]]:
        """Determine which items to keep, remove, or merge."""
        all_item_ids = {item.get("item_id") for item in items}
        items_to_remove: Set[str] = set()
        items_to_merge: List[Tuple[str, str]] = []

        for group in groups:
            if group.recommendation == RemovalAction.REMOVE:
                items_to_remove.update(group.duplicate_item_ids)

            elif group.recommendation == RemovalAction.MERGE:
                for dup_id in group.duplicate_item_ids:
                    items_to_merge.append((dup_id, group.primary_item_id))
                    items_to_remove.add(dup_id)

            elif group.recommendation == RemovalAction.KEEP_REFERENCE:
                # Keep only for reference, but still count as removed for package
                items_to_remove.update(group.duplicate_item_ids)

        items_to_keep = list(all_item_ids - items_to_remove)

        return items_to_keep, list(items_to_remove), items_to_merge

    def get_deduplication_report(
        self,
        result: DeduplicationResult,
        language: str = "en"
    ) -> Dict[str, Any]:
        """Generate a report of deduplication results."""
        templates = {
            "en": {
                "title": "Evidence Deduplication Report",
                "summary": "Deduplication Summary",
                "original": "Original items",
                "removed": "Removed items",
                "final": "Final items",
                "space_saved": "Space saved",
                "pages_saved": "Pages saved",
                "groups": "Duplicate Groups"
            },
            "de": {
                "title": "Bericht zur Duplikatenentfernung",
                "summary": "Zusammenfassung",
                "original": "Ursprüngliche Elemente",
                "removed": "Entfernte Elemente",
                "final": "Verbleibende Elemente",
                "space_saved": "Eingesparter Speicher",
                "pages_saved": "Eingesparte Seiten",
                "groups": "Duplikatgruppen"
            },
            "tr": {
                "title": "Tekrar Kaldırma Raporu",
                "summary": "Özet",
                "original": "Orijinal öğeler",
                "removed": "Kaldırılan öğeler",
                "final": "Son öğeler",
                "space_saved": "Kaydedilen alan",
                "pages_saved": "Kaydedilen sayfa",
                "groups": "Tekrar Grupları"
            }
        }

        t = templates.get(language, templates["en"])

        return {
            "title": t["title"],
            "summary": {
                t["original"]: result.original_count,
                t["removed"]: result.removed_count,
                t["final"]: result.final_count,
                t["space_saved"]: f"{result.space_saved_bytes / 1024:.1f} KB",
                t["pages_saved"]: result.pages_saved
            },
            "groups": [
                {
                    "type": group.similarity_type.value,
                    "primary": group.primary_item_id,
                    "duplicates": len(group.duplicate_item_ids),
                    "action": group.recommendation.value,
                    "explanation": group.explanation
                }
                for group in result.duplicate_groups
            ],
            "processing_time": f"{result.processing_time_seconds:.2f}s",
            "generated_at": result.created_at.isoformat()
        }

    def clear_cache(self):
        """Clear similarity cache."""
        self.similarity_cache.clear()
        self.content_hashes.clear()
        self.content_index.clear()
