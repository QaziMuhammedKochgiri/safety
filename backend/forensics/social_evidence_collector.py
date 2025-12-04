"""
Advanced Social Media Evidence Collector for SafeChild

This module provides forensic-grade evidence collection from multiple social media platforms.
Features:
- Multi-platform support (WhatsApp, Telegram, Instagram, Facebook, TikTok)
- Screenshot automation with legal metadata
- Evidence chain of custody tracking
- Cross-platform contact correlation
- Automated evidence packaging for court use
"""

import os
import json
import hashlib
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import httpx

# Try to import anthropic for AI-powered analysis
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


class Platform(str, Enum):
    """Supported social media platforms"""
    WHATSAPP = "whatsapp"
    TELEGRAM = "telegram"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    TIKTOK = "tiktok"
    EMAIL = "email"
    SMS = "sms"


class EvidenceType(str, Enum):
    """Types of evidence that can be collected"""
    MESSAGE = "message"
    MEDIA = "media"
    SCREENSHOT = "screenshot"
    CALL_LOG = "call_log"
    CONTACT = "contact"
    STORY = "story"
    POST = "post"
    LOCATION = "location"
    PROFILE = "profile"


class EvidenceStatus(str, Enum):
    """Status of evidence collection"""
    PENDING = "pending"
    COLLECTING = "collecting"
    COLLECTED = "collected"
    VERIFIED = "verified"
    FAILED = "failed"
    ARCHIVED = "archived"


@dataclass
class EvidenceMetadata:
    """Metadata for forensic evidence"""
    evidence_id: str
    platform: Platform
    evidence_type: EvidenceType
    collection_timestamp: str
    source_identifier: str  # Phone number, username, etc.
    file_hash_sha256: Optional[str] = None
    file_hash_md5: Optional[str] = None
    file_size_bytes: Optional[int] = None
    original_filename: Optional[str] = None
    collector_id: str = ""
    chain_of_custody: List[Dict] = None
    legal_notes: str = ""

    def __post_init__(self):
        if self.chain_of_custody is None:
            self.chain_of_custody = []

    def add_custody_entry(self, action: str, actor: str, notes: str = ""):
        """Add an entry to the chain of custody"""
        self.chain_of_custody.append({
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "actor": actor,
            "notes": notes
        })

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class CollectionSession:
    """Represents a social media evidence collection session"""
    session_id: str
    case_id: str
    client_number: str
    platforms: List[Platform]
    status: EvidenceStatus
    created_at: str
    updated_at: str
    created_by: str
    evidence_count: int = 0
    total_messages: int = 0
    total_media: int = 0
    contacts_found: int = 0
    risk_indicators: List[str] = None
    ai_analysis_completed: bool = False

    def __post_init__(self):
        if self.risk_indicators is None:
            self.risk_indicators = []


class SocialEvidenceCollector:
    """
    Advanced Social Media Evidence Collector

    Provides unified interface for collecting evidence from multiple platforms
    with forensic-grade metadata and chain of custody tracking.
    """

    def __init__(self, db):
        self.db = db
        self.anthropic_client = None

        if ANTHROPIC_AVAILABLE:
            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if api_key:
                self.anthropic_client = anthropic.AsyncAnthropic(api_key=api_key)

        # Service URLs
        self.whatsapp_url = os.environ.get("WHATSAPP_SERVICE_URL", "http://whatsapp-service:8002")
        self.telegram_url = os.environ.get("TELEGRAM_SERVICE_URL", "http://telegram-service:8003")

    async def create_collection_session(
        self,
        case_id: str,
        client_number: str,
        platforms: List[str],
        created_by: str,
        notes: str = ""
    ) -> Dict:
        """Create a new evidence collection session"""

        session_id = f"ECS-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{client_number[-4:]}"

        session = {
            "session_id": session_id,
            "case_id": case_id,
            "client_number": client_number,
            "platforms": platforms,
            "status": EvidenceStatus.PENDING.value,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "created_by": created_by,
            "notes": notes,
            "evidence_count": 0,
            "total_messages": 0,
            "total_media": 0,
            "contacts_found": 0,
            "platform_sessions": {},  # Store individual platform session IDs
            "risk_indicators": [],
            "ai_analysis_completed": False,
            "chain_of_custody": [
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "action": "session_created",
                    "actor": created_by,
                    "notes": f"Evidence collection session created for platforms: {', '.join(platforms)}"
                }
            ]
        }

        await self.db.evidence_sessions.insert_one(session)

        return session

    async def get_session(self, session_id: str) -> Optional[Dict]:
        """Get a collection session by ID"""
        return await self.db.evidence_sessions.find_one({"session_id": session_id})

    async def list_sessions(
        self,
        case_id: Optional[str] = None,
        client_number: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """List evidence collection sessions with optional filters"""

        query = {}
        if case_id:
            query["case_id"] = case_id
        if client_number:
            query["client_number"] = client_number
        if status:
            query["status"] = status

        cursor = self.db.evidence_sessions.find(query).sort("created_at", -1).limit(limit)
        return await cursor.to_list(length=limit)

    async def update_session_status(
        self,
        session_id: str,
        status: EvidenceStatus,
        actor: str,
        notes: str = ""
    ) -> bool:
        """Update session status and add custody entry"""

        session = await self.get_session(session_id)
        if not session:
            return False

        custody_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": f"status_changed_to_{status.value}",
            "actor": actor,
            "notes": notes
        }

        result = await self.db.evidence_sessions.update_one(
            {"session_id": session_id},
            {
                "$set": {
                    "status": status.value,
                    "updated_at": datetime.utcnow().isoformat()
                },
                "$push": {
                    "chain_of_custody": custody_entry
                }
            }
        )

        return result.modified_count > 0

    async def start_platform_collection(
        self,
        session_id: str,
        platform: str,
        actor: str,
        options: Dict = None
    ) -> Dict:
        """Start evidence collection for a specific platform"""

        session = await self.get_session(session_id)
        if not session:
            return {"success": False, "error": "Session not found"}

        if platform not in session["platforms"]:
            return {"success": False, "error": f"Platform {platform} not in session"}

        options = options or {}
        result = {"success": False, "platform": platform}

        try:
            if platform == Platform.WHATSAPP.value:
                result = await self._start_whatsapp_collection(session, options)
            elif platform == Platform.TELEGRAM.value:
                result = await self._start_telegram_collection(session, options)
            elif platform == Platform.INSTAGRAM.value:
                result = await self._start_instagram_collection(session, options)
            elif platform == Platform.FACEBOOK.value:
                result = await self._start_facebook_collection(session, options)
            elif platform == Platform.TIKTOK.value:
                result = await self._start_tiktok_collection(session, options)
            else:
                result = {"success": False, "error": f"Unsupported platform: {platform}"}

            if result.get("success"):
                # Update session with platform session ID
                await self.db.evidence_sessions.update_one(
                    {"session_id": session_id},
                    {
                        "$set": {
                            f"platform_sessions.{platform}": result.get("platform_session_id"),
                            "status": EvidenceStatus.COLLECTING.value,
                            "updated_at": datetime.utcnow().isoformat()
                        },
                        "$push": {
                            "chain_of_custody": {
                                "timestamp": datetime.utcnow().isoformat(),
                                "action": f"collection_started_{platform}",
                                "actor": actor,
                                "notes": f"Platform session: {result.get('platform_session_id')}"
                            }
                        }
                    }
                )

            return result

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _start_whatsapp_collection(self, session: Dict, options: Dict) -> Dict:
        """Start WhatsApp evidence collection"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.whatsapp_url}/session/start",
                    json={
                        "clientNumber": session["client_number"],
                        "caseId": session["case_id"],
                        "usePairingCode": options.get("use_pairing_code", True),
                        "phoneNumber": options.get("phone_number")
                    },
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()

                return {
                    "success": True,
                    "platform": "whatsapp",
                    "platform_session_id": data.get("sessionId"),
                    "status": data.get("status", "initializing")
                }
        except Exception as e:
            return {"success": False, "platform": "whatsapp", "error": str(e)}

    async def _start_telegram_collection(self, session: Dict, options: Dict) -> Dict:
        """Start Telegram evidence collection"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.telegram_url}/session/start",
                    json={
                        "clientNumber": session["client_number"],
                        "caseId": session["case_id"]
                    },
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()

                return {
                    "success": True,
                    "platform": "telegram",
                    "platform_session_id": data.get("sessionId"),
                    "status": data.get("status", "initializing")
                }
        except Exception as e:
            return {"success": False, "platform": "telegram", "error": str(e)}

    async def _start_instagram_collection(self, session: Dict, options: Dict) -> Dict:
        """
        Instagram evidence collection

        Note: Instagram requires OAuth or manual screenshot collection
        This creates a manual collection task for the admin
        """
        # Create a manual collection task
        task_id = f"IG-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        await self.db.collection_tasks.insert_one({
            "task_id": task_id,
            "session_id": session["session_id"],
            "platform": "instagram",
            "type": "manual_collection",
            "status": "pending",
            "created_at": datetime.utcnow().isoformat(),
            "instructions": {
                "de": """
                Instagram Beweissicherung:
                1. Öffnen Sie Instagram im Browser
                2. Navigieren Sie zu den relevanten DMs/Stories
                3. Verwenden Sie die Screenshot-Funktion des Systems
                4. Alle Screenshots werden automatisch mit Metadaten versehen
                """,
                "en": """
                Instagram Evidence Collection:
                1. Open Instagram in browser
                2. Navigate to relevant DMs/Stories
                3. Use the system's screenshot function
                4. All screenshots will be automatically tagged with metadata
                """
            },
            "target_username": options.get("target_username"),
            "evidence_types": options.get("evidence_types", ["dm", "story", "post", "profile"])
        })

        return {
            "success": True,
            "platform": "instagram",
            "platform_session_id": task_id,
            "status": "manual_collection_required",
            "instructions": "Manual collection task created. Admin will be notified."
        }

    async def _start_facebook_collection(self, session: Dict, options: Dict) -> Dict:
        """
        Facebook/Messenger evidence collection

        Similar to Instagram, requires OAuth or manual collection
        """
        task_id = f"FB-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        await self.db.collection_tasks.insert_one({
            "task_id": task_id,
            "session_id": session["session_id"],
            "platform": "facebook",
            "type": "manual_collection",
            "status": "pending",
            "created_at": datetime.utcnow().isoformat(),
            "instructions": {
                "de": """
                Facebook/Messenger Beweissicherung:
                1. Öffnen Sie Facebook Messenger im Browser
                2. Navigieren Sie zu den relevanten Konversationen
                3. Verwenden Sie die Screenshot-Funktion des Systems
                4. Alle Screenshots werden automatisch mit Metadaten versehen
                """,
                "en": """
                Facebook/Messenger Evidence Collection:
                1. Open Facebook Messenger in browser
                2. Navigate to relevant conversations
                3. Use the system's screenshot function
                4. All screenshots will be automatically tagged with metadata
                """
            },
            "target_username": options.get("target_username"),
            "evidence_types": options.get("evidence_types", ["message", "post", "profile"])
        })

        return {
            "success": True,
            "platform": "facebook",
            "platform_session_id": task_id,
            "status": "manual_collection_required",
            "instructions": "Manual collection task created. Admin will be notified."
        }

    async def _start_tiktok_collection(self, session: Dict, options: Dict) -> Dict:
        """TikTok evidence collection via URL archiving"""
        task_id = f"TT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        await self.db.collection_tasks.insert_one({
            "task_id": task_id,
            "session_id": session["session_id"],
            "platform": "tiktok",
            "type": "url_archive",
            "status": "pending",
            "created_at": datetime.utcnow().isoformat(),
            "urls": options.get("urls", []),
            "target_username": options.get("target_username"),
            "evidence_types": options.get("evidence_types", ["video", "comment", "profile"])
        })

        return {
            "success": True,
            "platform": "tiktok",
            "platform_session_id": task_id,
            "status": "archiving",
            "instructions": "TikTok content will be archived. Provide URLs to collect."
        }

    async def add_evidence(
        self,
        session_id: str,
        platform: str,
        evidence_type: str,
        content: Dict,
        source_identifier: str,
        actor: str,
        file_path: Optional[str] = None
    ) -> Dict:
        """Add evidence to a collection session"""

        evidence_id = f"EVD-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')[:17]}"

        # Calculate file hashes if file exists
        file_hash_sha256 = None
        file_hash_md5 = None
        file_size = None

        if file_path and os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                file_content = f.read()
                file_hash_sha256 = hashlib.sha256(file_content).hexdigest()
                file_hash_md5 = hashlib.md5(file_content).hexdigest()
                file_size = len(file_content)

        evidence = {
            "evidence_id": evidence_id,
            "session_id": session_id,
            "platform": platform,
            "evidence_type": evidence_type,
            "content": content,
            "source_identifier": source_identifier,
            "file_path": file_path,
            "file_hash_sha256": file_hash_sha256,
            "file_hash_md5": file_hash_md5,
            "file_size_bytes": file_size,
            "collection_timestamp": datetime.utcnow().isoformat(),
            "collector_id": actor,
            "verified": False,
            "chain_of_custody": [
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "action": "evidence_collected",
                    "actor": actor,
                    "notes": f"Evidence collected from {platform}"
                }
            ]
        }

        await self.db.evidence_items.insert_one(evidence)

        # Update session counts
        update_fields = {"$inc": {"evidence_count": 1}}
        if evidence_type == EvidenceType.MESSAGE.value:
            update_fields["$inc"]["total_messages"] = 1
        elif evidence_type in [EvidenceType.MEDIA.value, EvidenceType.SCREENSHOT.value]:
            update_fields["$inc"]["total_media"] = 1
        elif evidence_type == EvidenceType.CONTACT.value:
            update_fields["$inc"]["contacts_found"] = 1

        await self.db.evidence_sessions.update_one(
            {"session_id": session_id},
            update_fields
        )

        return evidence

    async def get_evidence(self, evidence_id: str) -> Optional[Dict]:
        """Get a single evidence item"""
        return await self.db.evidence_items.find_one({"evidence_id": evidence_id})

    async def list_evidence(
        self,
        session_id: str,
        platform: Optional[str] = None,
        evidence_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """List evidence items for a session"""

        query = {"session_id": session_id}
        if platform:
            query["platform"] = platform
        if evidence_type:
            query["evidence_type"] = evidence_type

        cursor = self.db.evidence_items.find(query).sort("collection_timestamp", -1).limit(limit)
        return await cursor.to_list(length=limit)

    async def verify_evidence(
        self,
        evidence_id: str,
        actor: str,
        verification_notes: str = ""
    ) -> bool:
        """Mark evidence as verified and add custody entry"""

        evidence = await self.get_evidence(evidence_id)
        if not evidence:
            return False

        # Re-verify file hash if file exists
        if evidence.get("file_path") and os.path.exists(evidence["file_path"]):
            with open(evidence["file_path"], 'rb') as f:
                current_hash = hashlib.sha256(f.read()).hexdigest()
                if current_hash != evidence.get("file_hash_sha256"):
                    # Hash mismatch - evidence may have been tampered
                    await self.db.evidence_items.update_one(
                        {"evidence_id": evidence_id},
                        {
                            "$push": {
                                "chain_of_custody": {
                                    "timestamp": datetime.utcnow().isoformat(),
                                    "action": "verification_failed_hash_mismatch",
                                    "actor": actor,
                                    "notes": "File hash does not match original - possible tampering"
                                }
                            }
                        }
                    )
                    return False

        result = await self.db.evidence_items.update_one(
            {"evidence_id": evidence_id},
            {
                "$set": {"verified": True},
                "$push": {
                    "chain_of_custody": {
                        "timestamp": datetime.utcnow().isoformat(),
                        "action": "evidence_verified",
                        "actor": actor,
                        "notes": verification_notes or "Evidence integrity verified"
                    }
                }
            }
        )

        return result.modified_count > 0

    async def correlate_contacts(self, session_id: str) -> Dict:
        """
        Cross-platform contact correlation

        Finds contacts that appear across multiple platforms
        """

        session = await self.get_session(session_id)
        if not session:
            return {"error": "Session not found"}

        # Get all contacts from all platforms
        contacts = await self.db.evidence_items.find({
            "session_id": session_id,
            "evidence_type": EvidenceType.CONTACT.value
        }).to_list(length=1000)

        # Build contact map by phone number and name
        contact_map = {}
        for contact in contacts:
            content = contact.get("content", {})
            phone = content.get("phone_number", "").replace(" ", "").replace("-", "")
            name = content.get("name", "").lower().strip()

            if phone:
                if phone not in contact_map:
                    contact_map[phone] = {
                        "phone": phone,
                        "names": set(),
                        "platforms": set(),
                        "evidence_ids": []
                    }
                contact_map[phone]["names"].add(content.get("name", "Unknown"))
                contact_map[phone]["platforms"].add(contact["platform"])
                contact_map[phone]["evidence_ids"].append(contact["evidence_id"])

        # Find cross-platform contacts
        cross_platform = []
        for phone, data in contact_map.items():
            if len(data["platforms"]) > 1:
                cross_platform.append({
                    "phone": phone,
                    "names": list(data["names"]),
                    "platforms": list(data["platforms"]),
                    "evidence_count": len(data["evidence_ids"])
                })

        correlation_result = {
            "session_id": session_id,
            "total_contacts": len(contact_map),
            "cross_platform_contacts": len(cross_platform),
            "cross_platform_details": cross_platform,
            "analyzed_at": datetime.utcnow().isoformat()
        }

        # Store correlation result
        await self.db.evidence_sessions.update_one(
            {"session_id": session_id},
            {"$set": {"contact_correlation": correlation_result}}
        )

        return correlation_result

    async def generate_evidence_package(
        self,
        session_id: str,
        actor: str,
        include_ai_analysis: bool = True
    ) -> Dict:
        """
        Generate a forensic evidence package for court use

        Creates a structured package with:
        - Evidence inventory
        - Chain of custody documentation
        - Hash verification report
        - Optional AI analysis summary
        """

        session = await self.get_session(session_id)
        if not session:
            return {"error": "Session not found"}

        # Get all evidence
        evidence_list = await self.list_evidence(session_id, limit=10000)

        # Generate inventory
        inventory = []
        for evidence in evidence_list:
            inventory.append({
                "evidence_id": evidence["evidence_id"],
                "platform": evidence["platform"],
                "type": evidence["evidence_type"],
                "collected_at": evidence["collection_timestamp"],
                "hash_sha256": evidence.get("file_hash_sha256"),
                "verified": evidence.get("verified", False)
            })

        # Calculate summary statistics
        platform_summary = {}
        type_summary = {}
        for item in inventory:
            platform_summary[item["platform"]] = platform_summary.get(item["platform"], 0) + 1
            type_summary[item["type"]] = type_summary.get(item["type"], 0) + 1

        package = {
            "package_id": f"PKG-{session_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "session_id": session_id,
            "case_id": session.get("case_id"),
            "client_number": session.get("client_number"),
            "generated_at": datetime.utcnow().isoformat(),
            "generated_by": actor,
            "summary": {
                "total_evidence_items": len(inventory),
                "total_messages": session.get("total_messages", 0),
                "total_media": session.get("total_media", 0),
                "contacts_found": session.get("contacts_found", 0),
                "platforms_collected": list(platform_summary.keys()),
                "platform_breakdown": platform_summary,
                "type_breakdown": type_summary,
                "verified_items": sum(1 for i in inventory if i["verified"]),
                "unverified_items": sum(1 for i in inventory if not i["verified"])
            },
            "chain_of_custody": session.get("chain_of_custody", []),
            "inventory": inventory,
            "contact_correlation": session.get("contact_correlation"),
            "risk_indicators": session.get("risk_indicators", [])
        }

        # Add AI analysis if requested and available
        if include_ai_analysis and self.anthropic_client:
            try:
                analysis = await self._generate_ai_package_summary(session, evidence_list)
                package["ai_analysis"] = analysis
            except Exception as e:
                package["ai_analysis_error"] = str(e)

        # Store package
        await self.db.evidence_packages.insert_one(package)

        # Add custody entry
        await self.db.evidence_sessions.update_one(
            {"session_id": session_id},
            {
                "$push": {
                    "chain_of_custody": {
                        "timestamp": datetime.utcnow().isoformat(),
                        "action": "evidence_package_generated",
                        "actor": actor,
                        "notes": f"Package ID: {package['package_id']}"
                    }
                }
            }
        )

        return package

    async def _generate_ai_package_summary(
        self,
        session: Dict,
        evidence_list: List[Dict]
    ) -> Dict:
        """Generate AI-powered summary of evidence package"""

        if not self.anthropic_client:
            return {"error": "AI not available"}

        # Prepare evidence summary for AI
        evidence_summary = []
        for evidence in evidence_list[:100]:  # Limit for context
            if evidence.get("evidence_type") == EvidenceType.MESSAGE.value:
                content = evidence.get("content", {})
                evidence_summary.append({
                    "platform": evidence["platform"],
                    "timestamp": content.get("timestamp"),
                    "sender": content.get("sender"),
                    "text": content.get("text", "")[:200]  # Truncate long messages
                })

        prompt = f"""Analyze this evidence collection summary for a family law case:

Case ID: {session.get('case_id')}
Platforms collected: {', '.join(session.get('platforms', []))}
Total messages: {session.get('total_messages', 0)}
Total media files: {session.get('total_media', 0)}
Contacts found: {session.get('contacts_found', 0)}

Sample of collected messages:
{json.dumps(evidence_summary[:20], indent=2, default=str)}

Provide a brief forensic summary including:
1. Overview of collected evidence
2. Any patterns or notable findings
3. Potential areas of concern for child welfare
4. Recommendations for further investigation

Keep the response concise and factual. This is for legal documentation."""

        try:
            response = await self.anthropic_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )

            return {
                "summary": response.content[0].text,
                "generated_at": datetime.utcnow().isoformat(),
                "model": "claude-sonnet-4-20250514"
            }
        except Exception as e:
            return {"error": str(e)}

    async def get_dashboard_stats(self) -> Dict:
        """Get dashboard statistics for evidence collection"""

        # Get session counts by status
        pipeline = [
            {"$group": {
                "_id": "$status",
                "count": {"$sum": 1}
            }}
        ]
        status_counts = await self.db.evidence_sessions.aggregate(pipeline).to_list(length=100)

        # Get platform usage
        platform_pipeline = [
            {"$unwind": "$platforms"},
            {"$group": {
                "_id": "$platforms",
                "count": {"$sum": 1}
            }}
        ]
        platform_counts = await self.db.evidence_sessions.aggregate(platform_pipeline).to_list(length=100)

        # Get recent sessions
        recent_sessions = await self.list_sessions(limit=5)

        # Get total evidence counts
        total_evidence = await self.db.evidence_items.count_documents({})
        verified_evidence = await self.db.evidence_items.count_documents({"verified": True})

        return {
            "session_stats": {status["_id"]: status["count"] for status in status_counts},
            "platform_usage": {p["_id"]: p["count"] for p in platform_counts},
            "total_sessions": await self.db.evidence_sessions.count_documents({}),
            "total_evidence_items": total_evidence,
            "verified_evidence": verified_evidence,
            "recent_sessions": [
                {
                    "session_id": s["session_id"],
                    "case_id": s.get("case_id"),
                    "platforms": s.get("platforms"),
                    "status": s.get("status"),
                    "created_at": s.get("created_at"),
                    "evidence_count": s.get("evidence_count", 0)
                }
                for s in recent_sessions
            ]
        }


class ScreenshotCollector:
    """
    Automated Screenshot Collector with Legal Metadata

    Creates forensic-grade screenshots with:
    - Timestamp watermark
    - URL/source verification
    - Hash for integrity verification
    - Chain of custody tracking
    """

    def __init__(self, db):
        self.db = db
        self.storage_path = os.environ.get("EVIDENCE_STORAGE_PATH", "/data/evidence/screenshots")

    async def capture_screenshot(
        self,
        session_id: str,
        platform: str,
        source_url: str,
        actor: str,
        notes: str = ""
    ) -> Dict:
        """
        Record a screenshot capture (actual capture done client-side)

        This method records the metadata and prepares for file upload
        """

        screenshot_id = f"SS-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')[:17]}"

        screenshot_record = {
            "screenshot_id": screenshot_id,
            "session_id": session_id,
            "platform": platform,
            "source_url": source_url,
            "capture_timestamp": datetime.utcnow().isoformat(),
            "captured_by": actor,
            "notes": notes,
            "status": "pending_upload",
            "file_path": None,
            "file_hash_sha256": None,
            "file_hash_md5": None,
            "metadata": {
                "user_agent": None,
                "viewport_size": None,
                "page_title": None
            },
            "chain_of_custody": [
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "action": "screenshot_initiated",
                    "actor": actor,
                    "notes": f"Screenshot of {source_url}"
                }
            ]
        }

        await self.db.screenshots.insert_one(screenshot_record)

        return screenshot_record

    async def upload_screenshot(
        self,
        screenshot_id: str,
        file_content: bytes,
        metadata: Dict,
        actor: str
    ) -> Dict:
        """Process uploaded screenshot file"""

        record = await self.db.screenshots.find_one({"screenshot_id": screenshot_id})
        if not record:
            return {"error": "Screenshot record not found"}

        # Calculate hashes
        file_hash_sha256 = hashlib.sha256(file_content).hexdigest()
        file_hash_md5 = hashlib.md5(file_content).hexdigest()

        # Create storage path
        date_path = datetime.utcnow().strftime("%Y/%m/%d")
        full_path = os.path.join(self.storage_path, record["session_id"], date_path)
        os.makedirs(full_path, exist_ok=True)

        filename = f"{screenshot_id}.png"
        file_path = os.path.join(full_path, filename)

        # Save file
        with open(file_path, 'wb') as f:
            f.write(file_content)

        # Update record
        await self.db.screenshots.update_one(
            {"screenshot_id": screenshot_id},
            {
                "$set": {
                    "status": "uploaded",
                    "file_path": file_path,
                    "file_hash_sha256": file_hash_sha256,
                    "file_hash_md5": file_hash_md5,
                    "file_size_bytes": len(file_content),
                    "metadata": metadata
                },
                "$push": {
                    "chain_of_custody": {
                        "timestamp": datetime.utcnow().isoformat(),
                        "action": "screenshot_uploaded",
                        "actor": actor,
                        "notes": f"File stored: {file_path}, SHA256: {file_hash_sha256}"
                    }
                }
            }
        )

        return {
            "success": True,
            "screenshot_id": screenshot_id,
            "file_path": file_path,
            "hash_sha256": file_hash_sha256
        }

    async def list_screenshots(
        self,
        session_id: str,
        platform: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """List screenshots for a session"""

        query = {"session_id": session_id}
        if platform:
            query["platform"] = platform

        cursor = self.db.screenshots.find(query).sort("capture_timestamp", -1).limit(limit)
        return await cursor.to_list(length=limit)
