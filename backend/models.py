from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict
from datetime import datetime, timezone
import uuid

# Client Model
class ClientCreate(BaseModel):
    firstName: str
    lastName: str
    email: EmailStr
    phone: str
    country: str
    caseType: str  # "hague_convention", "child_abduction", "custody_rights"

class Client(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    clientNumber: str
    firstName: str
    lastName: str
    email: EmailStr
    phone: str
    country: str
    caseType: str
    hashedPassword: Optional[str] = None  # For client portal login
    role: str = "client"  # "client" or "admin"
    status: str = "active"  # "active", "closed", "pending"
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updatedAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Document Model
class DocumentUpload(BaseModel):
    clientNumber: str

class Document(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    documentNumber: str
    clientNumber: str
    fileName: str
    fileSize: int
    fileType: str
    filePath: str
    uploadedBy: str = "client"  # "client" or "lawyer"
    uploadedAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = "pending"  # "pending", "reviewed", "approved"

# Consent Model
class LocationData(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    country: Optional[str] = None
    city: Optional[str] = None

class Permissions(BaseModel):
    location: bool
    browser: bool
    camera: bool
    files: bool
    forensic: bool

class ConsentCreate(BaseModel):
    sessionId: str
    permissions: Permissions
    location: Optional[LocationData] = None
    userAgent: str
    clientNumber: Optional[str] = None

class Consent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sessionId: str
    ipAddress: str
    userAgent: str
    location: Optional[LocationData] = None
    permissions: Permissions
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    clientNumber: Optional[str] = None

# Chat Message Model
class ChatMessageCreate(BaseModel):
    sessionId: str
    sender: str  # "client", "bot", "agent"
    message: str
    clientNumber: Optional[str] = None
    agentName: Optional[str] = None  # Name of the support agent
    isMobile: Optional[bool] = None
    language: Optional[str] = None

class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sessionId: str
    clientNumber: Optional[str] = None
    sender: str
    message: str
    agentName: Optional[str] = None  # Name of the support agent
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    isRead: bool = False

# Landmark Case Model (read-only)
class LandmarkCase(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    caseNumber: str
    year: int
    countries: Dict[str, str]
    title: Dict[str, str]
    description: Dict[str, str]
    outcome: Dict[str, str]
    facts: Dict[str, str]
    legalPrinciple: Dict[str, str]
    impact: Dict[str, str]

# Authentication Models
class ClientRegister(BaseModel):
    email: EmailStr
    password: str
    firstName: str
    lastName: str
    phone: str
    country: str
    caseType: str

class ClientLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    clientNumber: str
    email: str
    firstName: str
    lastName: str

# Meeting/Video Call Models
class MeetingCreate(BaseModel):
    title: str
    description: Optional[str] = None
    scheduledTime: Optional[datetime] = None
    duration: int = 60  # in minutes
    meetingType: str = "consultation"  # "consultation", "follow_up", "urgent"

class Meeting(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    meetingId: str
    clientNumber: str
    clientEmail: str
    title: str
    description: Optional[str] = None
    roomName: str
    meetingUrl: str
    scheduledTime: Optional[datetime] = None
    duration: int = 60
    meetingType: str = "consultation"
    status: str = "scheduled"  # "scheduled", "in_progress", "completed", "cancelled"
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updatedAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    startedAt: Optional[datetime] = None
    endedAt: Optional[datetime] = None

# Forensic & Chain of Custody Models
class ChainOfCustodyEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    actor: str  # e.g., "Client: John Doe", "System: SHA256 Verification", "Lawyer: Admin"
    action: str  # e.g., "UPLOAD", "HASH_VERIFICATION", "ACCESS", "REPORT_GENERATED"
    details: str
    ipAddress: Optional[str] = None
    hashAtEvent: Optional[str] = None  # File hash at this specific point

class ForensicCase(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    caseId: str  # Unique Case ID (e.g., CASE_20251128_XYZ)
    clientNumber: str
    caseStatus: str = "pending"  # pending, analyzing, completed, failed
    evidenceFiles: List[str] = []  # List of file paths/names
    primaryFileHash: Optional[str] = None  # SHA-256 Hash of the main evidence
    chainOfCustody: List[ChainOfCustodyEvent] = []
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updatedAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class EvidenceRequest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    token: str # Unique access token for the magic link
    clientNumber: str
    lawyerId: str # Which admin created this request
    requestedTypes: List[str] = [] # e.g. ["photos", "documents", "whatsapp_backup"]
    scenario_type: Optional[str] = "standard"  # standard (tech_savvy), elderly (one-click), chat_only
    status: str = "pending" # pending, completed, expired
    expiresAt: datetime
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SharedReportLink(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    token: str  # Unique token for URL
    caseId: str
    generatedBy: str  # Admin who generated it
    expiresAt: datetime
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    isRevoked: bool = False

# ============================================================================
# Phone Recovery Models
# ============================================================================

class DeviceInfo(BaseModel):
    device_type: str  # "android" | "ios"
    device_model: Optional[str] = None
    os_version: Optional[str] = None
    serial_number: Optional[str] = None
    storage_total: Optional[int] = None  # in bytes
    connection_type: str  # "usb" | "wireless"

class DataCategories(BaseModel):
    photos: bool = True
    videos: bool = True
    messages: bool = True
    contacts: bool = True
    call_logs: bool = True
    deleted_data: bool = True
    app_data: bool = True

class BackupFileInfo(BaseModel):
    file_name: str
    file_size: int
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    checksum_sha256: Optional[str] = None
    encrypted_path: Optional[str] = None
    encryption_metadata: Optional[Dict] = None

class RecoveryStatistics(BaseModel):
    photos: int = 0
    videos: int = 0
    messages: int = 0
    contacts: int = 0
    call_logs: int = 0
    deleted_files: int = 0
    app_files: int = 0
    total_size: int = 0

class ProcessedData(BaseModel):
    extracted_dir: Optional[str] = None
    statistics: Optional[RecoveryStatistics] = None
    deleted_files_recovered: int = 0
    processing_time_seconds: int = 0

class RecoveryResults(BaseModel):
    zip_path: Optional[str] = None
    zip_size: int = 0
    checksum_sha256: Optional[str] = None
    encrypted: bool = True

class DeletionSchedule(BaseModel):
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    auto_delete_at: datetime  # 15 days from creation
    deleted_at: Optional[datetime] = None

class RecoveryCustodyEvent(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    actor: str  # "Admin: user@example.com" | "Client: client@example.com" | "System"
    action: str  # "LINK_CREATED", "DEVICE_CONNECTED", "BACKUP_UPLOADED", etc.
    details: str

class PhoneRecoveryCase(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    case_id: str  # "RECOVERY_SC2025001_20251217"
    client_number: str
    recovery_method: str  # "usb" | "wireless"

    # Wireless recovery fields
    recovery_code: Optional[str] = None  # 8-char short code for client
    full_token: Optional[str] = None  # Full UUID token
    expires_at: Optional[datetime] = None

    # Device information
    device_info: Optional[DeviceInfo] = None

    # Recovery options
    data_categories: DataCategories = Field(default_factory=DataCategories)

    # Status tracking
    status: str = "pending"  # "pending" | "backup_ready" | "processing" | "completed" | "failed" | "expired"
    progress_percent: int = 0
    current_step: Optional[str] = None

    # Backup file (for wireless recovery)
    backup_file: Optional[BackupFileInfo] = None

    # Processing results
    processed: Optional[ProcessedData] = None

    # Results package
    results: Optional[RecoveryResults] = None

    # Auto-deletion schedule (15 days)
    deletion_schedule: Optional[DeletionSchedule] = None

    # Chain of custody audit trail
    chain_of_custody: List[RecoveryCustodyEvent] = []

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None

class RecoveryProcessingJob(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    job_id: str
    case_id: str  # References PhoneRecoveryCase.case_id

    status: str = "queued"  # "queued" | "extracting" | "carving" | "packaging" | "completed" | "failed"
    progress_percent: int = 0
    current_step: Optional[str] = None

    started_at: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    errors: List[Dict] = []  # [{timestamp, message, severity}]

# Request/Response models for API
class CreateRecoveryLinkRequest(BaseModel):
    client_number: str
    device_type: str = "auto"  # "android" | "ios" | "auto" (auto-detect on client)
    data_categories: Optional[DataCategories] = None
    expires_in_days: int = 15

class CreateRecoveryLinkResponse(BaseModel):
    case_id: str
    recovery_code: str  # 8-char short code
    recovery_link: str  # Full URL for client
    apk_download_link: Optional[str] = None  # Android APK download
    expires_at: datetime

class USBDeviceInfo(BaseModel):
    device_id: str
    device_type: str  # "android" | "ios"
    device_model: Optional[str] = None
    serial_number: Optional[str] = None
    is_authorized: bool = False
    storage_info: Optional[Dict] = None

class StartUSBRecoveryRequest(BaseModel):
    device_id: str
    client_number: str
    data_categories: Optional[DataCategories] = None

class RecoveryStatusResponse(BaseModel):
    case_id: str
    status: str
    progress_percent: int
    current_step: Optional[str] = None
    statistics: Optional[RecoveryStatistics] = None
    download_ready: bool = False
